/* -*- P4_16 -*- */
/*
 * P4-Based Network Monitoring Tool
 * Main monitoring program for packet processing and feature extraction
 */

#include <core.p4>
#include <v1model.p4>

#include "includes/headers.p4"
#include "includes/metadata.p4"

/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol) {
            TYPE_TCP: parse_tcp;
            TYPE_UDP: parse_udp;
            TYPE_ICMP: parse_icmp;
            default: accept;
        }
    }

    state parse_tcp {
        packet.extract(hdr.tcp);
        transition accept;
    }

    state parse_udp {
        packet.extract(hdr.udp);
        transition accept;
    }
    
    state parse_icmp {
        packet.extract(hdr.icmp);
        transition accept;
    }
}

/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}

/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    // Registers for flow tracking
    register<bit<32>>(65536) flow_packet_count;
    register<bit<32>>(65536) flow_byte_count;
    register<bit<48>>(65536) flow_start_time;
    register<bit<48>>(65536) flow_last_seen;
    
    // Counters for statistics
    counter(65536, CounterType.packets_and_bytes) flow_stats;
    counter(1024, CounterType.packets_and_bytes) protocol_stats;
    
    // Hash for flow identification
    action compute_flow_hash() {
        bit<16> src_port = 0;
        bit<16> dst_port = 0;
        
        if (hdr.tcp.isValid()) {
            src_port = hdr.tcp.srcPort;
            dst_port = hdr.tcp.dstPort;
        } else if (hdr.udp.isValid()) {
            src_port = hdr.udp.srcPort;
            dst_port = hdr.udp.dstPort;
        }
        
        hash(meta.flow_meta.flow_id,
             HashAlgorithm.crc32,
             (bit<32>)0,
             { hdr.ipv4.srcAddr,
               hdr.ipv4.dstAddr,
               hdr.ipv4.protocol,
               src_port,
               dst_port },
             (bit<32>)65536);
    }
    
    action extract_packet_features() {
        // Extract packet size
        meta.monitor_meta.packet_size = standard_metadata.packet_length;
        
        // Record timestamp
        meta.flow_meta.timestamp = standard_metadata.ingress_global_timestamp;
        
        // Update flow statistics
        bit<32> packet_count;
        bit<32> byte_count;
        bit<48> start_time;
        bit<48> last_seen;
        
        flow_packet_count.read(packet_count, meta.flow_meta.flow_id);
        flow_byte_count.read(byte_count, meta.flow_meta.flow_id);
        flow_start_time.read(start_time, meta.flow_meta.flow_id);
        flow_last_seen.read(last_seen, meta.flow_meta.flow_id);
        
        // Initialize new flow
        if (packet_count == 0) {
            flow_start_time.write(meta.flow_meta.flow_id, meta.flow_meta.timestamp);
            start_time = meta.flow_meta.timestamp;
        }
        
        // Update counters
        packet_count = packet_count + 1;
        byte_count = byte_count + (bit<32>)standard_metadata.packet_length;
        
        flow_packet_count.write(meta.flow_meta.flow_id, packet_count);
        flow_byte_count.write(meta.flow_meta.flow_id, byte_count);
        flow_last_seen.write(meta.flow_meta.flow_id, meta.flow_meta.timestamp);
        
        // Update metadata
        meta.flow_meta.packet_count = packet_count;
        meta.flow_meta.byte_count = byte_count;
        meta.flow_meta.flow_duration = (bit<16>)(meta.flow_meta.timestamp - start_time);
        
        // Update P4 counters
        flow_stats.count(meta.flow_meta.flow_id);
        protocol_stats.count((bit<32>)hdr.ipv4.protocol);
    }
    
    action set_sampling() {
        // Simple sampling logic (sample every 10th packet for demo)
        if (meta.flow_meta.packet_count % 10 == 1) {
            meta.monitor_meta.export_flag = 1;
        } else {
            meta.monitor_meta.export_flag = 0;
        }
    }
    
    // Flow identification table with 5-tuple matching
    table flow_table {
        key = {
            hdr.ipv4.srcAddr: exact;
            hdr.ipv4.dstAddr: exact;
            hdr.ipv4.protocol: exact;
            hdr.tcp.srcPort: exact @name("tcp_src_port");
            hdr.tcp.dstPort: exact @name("tcp_dst_port");
            hdr.udp.srcPort: exact @name("udp_src_port");
            hdr.udp.dstPort: exact @name("udp_dst_port");
        }
        actions = {
            NoAction;
        }
        size = 65536;
        default_action = NoAction();
    }
    
    // Protocol-based monitoring policies
    table monitoring_policy {
        key = {
            hdr.ipv4.protocol: exact;
        }
        actions = {
            set_sampling;
            NoAction;
        }
        size = 256;
        default_action = set_sampling();
    }

    apply {
        if (hdr.ipv4.isValid()) {
            // Compute flow hash for identification
            compute_flow_hash();
            
            // Extract packet features and update flow state
            extract_packet_features();
            
            // Apply monitoring policy
            monitoring_policy.apply();
            
            // Check flow table (for future flow-specific rules)
            flow_table.apply();
            
            // Forward packet normally
            standard_metadata.egress_spec = standard_metadata.ingress_port;
        }
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

// Digest structure for flow export
struct flow_digest_t {
    bit<32> flow_id;
    bit<32> src_ip;
    bit<32> dst_ip;
    bit<8>  protocol;
    bit<16> src_port;
    bit<16> dst_port;
    bit<32> packet_count;
    bit<32> byte_count;
    bit<48> timestamp;
    bit<16> flow_duration;
    bit<16> packet_size;
}

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
    
    apply {
        // Export flow information via digest if sampling flag is set
        if (meta.monitor_meta.export_flag == 1 && hdr.ipv4.isValid()) {
            bit<16> src_port = 0;
            bit<16> dst_port = 0;
            
            if (hdr.tcp.isValid()) {
                src_port = hdr.tcp.srcPort;
                dst_port = hdr.tcp.dstPort;
            } else if (hdr.udp.isValid()) {
                src_port = hdr.udp.srcPort;
                dst_port = hdr.udp.dstPort;
            }
            
            flow_digest_t flow_data = {
                meta.flow_meta.flow_id,
                hdr.ipv4.srcAddr,
                hdr.ipv4.dstAddr,
                hdr.ipv4.protocol,
                src_port,
                dst_port,
                meta.flow_meta.packet_count,
                meta.flow_meta.byte_count,
                meta.flow_meta.timestamp,
                meta.flow_meta.flow_duration,
                meta.monitor_meta.packet_size
            };
            
            digest<flow_digest_t>(1, flow_data);
        }
    }
}

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers hdr, inout metadata meta) {
     apply {
        update_checksum(
            hdr.ipv4.isValid(),
            { hdr.ipv4.version,
              hdr.ipv4.ihl,
              hdr.ipv4.diffserv,
              hdr.ipv4.totalLen,
              hdr.ipv4.identification,
              hdr.ipv4.flags,
              hdr.ipv4.fragOffset,
              hdr.ipv4.ttl,
              hdr.ipv4.protocol,
              hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16);
    }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.tcp);
        packet.emit(hdr.udp);
        packet.emit(hdr.icmp);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;