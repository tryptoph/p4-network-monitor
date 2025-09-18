/* -*- P4_16 -*- */
/*
 * Metadata definitions for network monitoring
 */

#ifndef __METADATA_P4__
#define __METADATA_P4__

struct flow_metadata_t {
    bit<32> flow_id;
    bit<48> timestamp;
    bit<32> packet_count;
    bit<32> byte_count;
    bit<16> flow_duration;
}

struct monitoring_metadata_t {
    bit<16> packet_size;
    bit<8>  sampling_rate;
    bit<1>  export_flag;
}

struct metadata {
    flow_metadata_t       flow_meta;
    monitoring_metadata_t monitor_meta;
}

#endif