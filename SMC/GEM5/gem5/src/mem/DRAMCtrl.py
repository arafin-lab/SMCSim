# Copyright (c) 2012-2014 ARM Limited
# All rights reserved.
#
# The license below extends only to copyright in the software and shall
# not be construed as granting a license to any other intellectual
# property including but not limited to intellectual property relating
# to a hardware implementation of the functionality of the software
# licensed hereunder.  You may use the software subject to the license
# terms below provided that you ensure that this notice is replicated
# unmodified and in its entirety in all distributions of the software,
# modified or unmodified, in source code or in binary form.
#
# Copyright (c) 2013 Amin Farmahini-Farahani
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Authors: Andreas Hansson
#          Ani Udipi

from m5.params import *
from AbstractMemory import *

# Enum for memory scheduling algorithms, currently First-Come
# First-Served and a First-Row Hit then First-Come First-Served
class MemSched(Enum): vals = ['fcfs', 'frfcfs']

# Enum for the address mapping. With Ch, Ra, Ba, Ro and Co denoting
# channel, rank, bank, row and column, respectively, and going from
# MSB to LSB.  Available are RoRaBaChCo and RoRaBaCoCh, that are
# suitable for an open-page policy, optimising for sequential accesses
# hitting in the open row. For a closed-page policy, RoCoRaBaCh
# maximises parallelism.
class AddrMap(Enum): vals = ['RoRaBaChCo', 'RoRaBaCoCh', 'RoCoRaBaCh']

# Enum for the page policy, either open, open_adaptive, close, or
# close_adaptive.
class PageManage(Enum): vals = ['open', 'open_adaptive', 'close',
                                'close_adaptive']

# DRAMCtrl is a single-channel single-ported DRAM controller model
# that aims to model the most important system-level performance
# effects of a DRAM without getting into too much detail of the DRAM
# itself.
class DRAMCtrl(AbstractMemory):
    type = 'DRAMCtrl'
    cxx_header = "mem/dram_ctrl.hh"

    # single-ported on the system interface side, instantiate with a
    # bus in front of the controller for multiple ports
    port = SlavePort("Slave port")

    # the basic configuration of the controller architecture
    write_buffer_size = Param.Unsigned(64, "Number of write queue entries")
    read_buffer_size = Param.Unsigned(32, "Number of read queue entries")

    # threshold in percent for when to forcefully trigger writes and
    # start emptying the write buffer
    write_high_thresh_perc = Param.Percent(85, "Threshold to force writes")

    # threshold in percentage for when to start writes if the read
    # queue is empty
    write_low_thresh_perc = Param.Percent(50, "Threshold to start writes")

    # minimum write bursts to schedule before switching back to reads
    min_writes_per_switch = Param.Unsigned(16, "Minimum write bursts before "
                                           "switching to reads")

    # scheduler, address map and page policy
    mem_sched_policy = Param.MemSched('frfcfs', "Memory scheduling policy")
    addr_mapping = Param.AddrMap('RoRaBaChCo', "Address mapping policy")
    page_policy = Param.PageManage('open_adaptive', "Page management policy")

    # enforce a limit on the number of accesses per row
    max_accesses_per_row = Param.Unsigned(16, "Max accesses per row before "
                                          "closing");

    # size of DRAM Chip in Bytes
    device_size = Param.MemorySize("Size of DRAM chip")

    # pipeline latency of the controller and PHY, split into a
    # frontend part and a backend part, with reads and writes serviced
    # by the queues only seeing the frontend contribution, and reads
    # serviced by the memory seeing the sum of the two
    static_frontend_latency = Param.Latency("10ns", "Static frontend latency")
    static_backend_latency = Param.Latency("10ns", "Static backend latency")

    # the physical organisation of the DRAM
    device_bus_width = Param.Unsigned("data bus width in bits for each DRAM "\
                                      "device/chip")
    burst_length = Param.Unsigned("Burst lenght (BL) in beats")
    device_rowbuffer_size = Param.MemorySize("Page (row buffer) size per "\
                                           "device/chip")
    devices_per_rank = Param.Unsigned("Number of devices/chips per rank")
    ranks_per_channel = Param.Unsigned("Number of ranks per channel")

    # default to 0 bank groups per rank, indicating bank group architecture
    # is not used
    # update per memory class when bank group architecture is supported
    bank_groups_per_rank = Param.Unsigned(0, "Number of bank groups per rank")
    banks_per_rank = Param.Unsigned("Number of banks per rank")
    # only used for the address mapping as the controller by
    # construction is a single channel and multiple controllers have
    # to be instantiated for a multi-channel configuration
    channels = Param.Unsigned(1, "Number of channels")

    # For power modelling we need to know if the DRAM has a DLL or not
    dll = Param.Bool(True, "DRAM has DLL or not")

    # DRAMPower provides in addition to the core power, the possibility to
    # include RD/WR termination and IO power. This calculation assumes some
    # default values. The integration of DRAMPower with gem5 does not include
    # IO and RD/WR termination power by default. This might be added as an
    # additional feature in the future.

    # timing behaviour and constraints - all in nanoseconds

    # the base clock period of the DRAM
    tCK = Param.Latency("Clock period")

    # the amount of time in nanoseconds from issuing an activate command
    # to the data being available in the row buffer for a read/write
    tRCD = Param.Latency("RAS to CAS delay")

    # the time from issuing a read/write command to seeing the actual data
    tCL = Param.Latency("CAS latency")

    # minimum time between a precharge and subsequent activate
    tRP = Param.Latency("Row precharge time")

    # minimum time between an activate and a precharge to the same row
    tRAS = Param.Latency("ACT to PRE delay")

    # minimum time between a write data transfer and a precharge
    tWR = Param.Latency("Write recovery time")

    # minimum time between a read and precharge command
    tRTP = Param.Latency("Read to precharge")

    # time to complete a burst transfer, typically the burst length
    # divided by two due to the DDR bus, but by making it a parameter
    # it is easier to also evaluate SDR memories like WideIO.
    # This parameter has to account for burst length.
    # Read/Write requests with data size larger than one full burst are broken
    # down into multiple requests in the controller
    # tBURST is equivalent to the CAS-to-CAS delay (tCCD)
    # With bank group architectures, tBURST represents the CAS-to-CAS
    # delay for bursts to different bank groups (tCCD_S)
    tBURST = Param.Latency("Burst duration (for DDR burst length / 2 cycles)")

    # CAS-to-CAS delay for bursts to the same bank group
    # only utilized with bank group architectures; set to 0 for default case
    # tBURST is equivalent to tCCD_S; no explicit parameter required
    # for CAS-to-CAS delay for bursts to different bank groups
    tCCD_L = Param.Latency("0ns", "Same bank group CAS to CAS delay")

    # time taken to complete one refresh cycle (N rows in all banks)
    tRFC = Param.Latency("Refresh cycle time")

    # refresh command interval, how often a "ref" command needs
    # to be sent. It is 7.8 us for a 64ms refresh requirement
    tREFI = Param.Latency("Refresh command interval")

    # write-to-read, same rank turnaround penalty
    tWTR = Param.Latency("Write to read, same rank switching time")

    # read-to-write, same rank turnaround penalty
    tRTW = Param.Latency("Read to write, same rank switching time")

    # rank-to-rank bus delay penalty
    # this does not correlate to a memory timing parameter and encompasses:
    # 1) RD-to-RD, 2) WR-to-WR, 3) RD-to-WR, and 4) WR-to-RD
    # different rank bus delay
    tCS = Param.Latency("Rank to rank switching time")

    # minimum row activate to row activate delay time
    tRRD = Param.Latency("ACT to ACT delay")

    # only utilized with bank group architectures; set to 0 for default case
    tRRD_L = Param.Latency("0ns", "Same bank group ACT to ACT delay")

    # time window in which a maximum number of activates are allowed
    # to take place, set to 0 to disable
    tXAW = Param.Latency("X activation window")
    activation_limit = Param.Unsigned("Max number of activates in window")

    # time to exit power-down mode
    # Exit power-down to next valid command delay
    tXP = Param.Latency("0ns", "Power-up Delay")

    # Exit Powerdown to commands requiring a locked DLL
    tXPDLL = Param.Latency("0ns", "Power-up Delay with locked DLL")

    # time to exit self-refresh mode
    tXS = Param.Latency("0ns", "Self-refresh exit latency")

    # time to exit self-refresh mode with locked DLL
    tXSDLL = Param.Latency("0ns", "Self-refresh exit latency DLL")

    # Currently rolled into other params
    ######################################################################

    # tRC  - assumed to be tRAS + tRP

    # Power Behaviour and Constraints
    # DRAMs like LPDDR and WideIO have 2 external voltage domains. These are
    # defined as VDD and VDD2. Each current is defined for each voltage domain
    # separately. For example, current IDD0 is active-precharge current for
    # voltage domain VDD and current IDD02 is active-precharge current for
    # voltage domain VDD2.
    # By default all currents are set to 0mA. Users who are only interested in
    # the performance of DRAMs can leave them at 0.

    # Operating 1 Bank Active-Precharge current
    IDD0 = Param.Current("0mA", "Active precharge current")

    # Operating 1 Bank Active-Precharge current multiple voltage Range
    IDD02 = Param.Current("0mA", "Active precharge current VDD2")

    # Precharge Power-down Current: Slow exit
    IDD2P0 = Param.Current("0mA", "Precharge Powerdown slow")

    # Precharge Power-down Current: Slow exit multiple voltage Range
    IDD2P02 = Param.Current("0mA", "Precharge Powerdown slow VDD2")

    # Precharge Power-down Current: Fast exit
    IDD2P1 = Param.Current("0mA", "Precharge Powerdown fast")

    # Precharge Power-down Current: Fast exit multiple voltage Range
    IDD2P12 = Param.Current("0mA", "Precharge Powerdown fast VDD2")

    # Precharge Standby current
    IDD2N = Param.Current("0mA", "Precharge Standby current")

    # Precharge Standby current multiple voltage range
    IDD2N2 = Param.Current("0mA", "Precharge Standby current VDD2")

    # Active Power-down current: slow exit
    IDD3P0 = Param.Current("0mA", "Active Powerdown slow")

    # Active Power-down current: slow exit multiple voltage range
    IDD3P02 = Param.Current("0mA", "Active Powerdown slow VDD2")

    # Active Power-down current : fast exit
    IDD3P1 = Param.Current("0mA", "Active Powerdown fast")

    # Active Power-down current : fast exit multiple voltage range
    IDD3P12 = Param.Current("0mA", "Active Powerdown fast VDD2")

    # Active Standby current
    IDD3N = Param.Current("0mA", "Active Standby current")

    # Active Standby current multiple voltage range
    IDD3N2 = Param.Current("0mA", "Active Standby current VDD2")

    # Burst Read Operating Current
    IDD4R = Param.Current("0mA", "READ current")

    # Burst Read Operating Current multiple voltage range
    IDD4R2 = Param.Current("0mA", "READ current VDD2")

    # Burst Write Operating Current
    IDD4W = Param.Current("0mA", "WRITE current")

    # Burst Write Operating Current multiple voltage range
    IDD4W2 = Param.Current("0mA", "WRITE current VDD2")

    # Refresh Current
    IDD5 = Param.Current("0mA", "Refresh current")

    # Refresh Current multiple voltage range
    IDD52 = Param.Current("0mA", "Refresh current VDD2")

    # Self-Refresh Current
    IDD6 = Param.Current("0mA", "Self-refresh Current")

    # Self-Refresh Current multiple voltage range
    IDD62 = Param.Current("0mA", "Self-refresh Current VDD2")

    # Main voltage range of the DRAM
    VDD = Param.Voltage("0V", "Main Voltage Range")

    # Second voltage range defined by some DRAMs
    VDD2 = Param.Voltage("0V", "2nd Voltage Range")

# A single DDR3-1600 x64 channel (one command and address bus), with
# timings based on a DDR3-1600 4 Gbit datasheet (Micron MT41J512M8) in
# an 8x8 configuration.
class DDR3_1600_x64(DRAMCtrl):
    # size of device in bytes
    device_size = '512MB'

    # 8x8 configuration, 8 devices each with an 8-bit interface
    device_bus_width = 8

    # DDR3 is a BL8 device
    burst_length = 8

    # Each device has a page (row buffer) size of 1 Kbyte (1K columns x8)
    device_rowbuffer_size = '1kB'

    # 8x8 configuration, so 8 devices
    devices_per_rank = 8

    # Use two ranks
    ranks_per_channel = 2

    # DDR3 has 8 banks in all configurations
    banks_per_rank = 8

    # 800 MHz
    tCK = '1.25ns'

    # 8 beats across an x64 interface translates to 4 clocks @ 800 MHz
    tBURST = '5ns'

    # DDR3-1600 11-11-11
    tRCD = '13.75ns'
    tCL = '13.75ns'
    tRP = '13.75ns'
    tRAS = '35ns'
    tRRD = '6ns'
    tXAW = '30ns'
    activation_limit = 4
    tRFC = '260ns'

    tWR = '15ns'

    # Greater of 4 CK or 7.5 ns
    tWTR = '7.5ns'

    # Greater of 4 CK or 7.5 ns
    tRTP = '7.5ns'

    # Default same rank rd-to-wr bus turnaround to 2 CK, @800 MHz = 2.5 ns
    tRTW = '2.5ns'

    # Default different rank bus delay to 2 CK, @800 MHz = 2.5 ns
    tCS = '2.5ns'

    # <=85C, half for >85C
    tREFI = '7.8us'

    # Current values from datasheet
    IDD0 = '75mA'
    IDD2N = '50mA'
    IDD3N = '57mA'
    IDD4W = '165mA'
    IDD4R = '187mA'
    IDD5 = '220mA'
    VDD = '1.5V'

# A single DDR3-2133 x64 channel refining a selected subset of the
# options for the DDR-1600 configuration, based on the same DDR3-1600
# 4 Gbit datasheet (Micron MT41J512M8). Most parameters are kept
# consistent across the two configurations.
class DDR3_2133_x64(DDR3_1600_x64):
    # 1066 MHz
    tCK = '0.938ns'

    # 8 beats across an x64 interface translates to 4 clocks @ 1066 MHz
    tBURST = '3.752ns'

    # DDR3-2133 14-14-14
    tRCD = '13.09ns'
    tCL = '13.09ns'
    tRP = '13.09ns'
    tRAS = '33ns'
    tRRD = '5ns'
    tXAW = '25ns'

    # Current values from datasheet
    IDD0 = '70mA'
    IDD2N = '37mA'
    IDD3N = '44mA'
    IDD4W = '157mA'
    IDD4R = '191mA'
    IDD5 = '250mA'
    VDD = '1.5V'

# A single DDR4-2400 x64 channel (one command and address bus), with
# timings based on a DDR4-2400 4 Gbit datasheet (Micron MT40A512M8)
# in an 8x8 configuration.
class DDR4_2400_x64(DRAMCtrl):
    # size of device
    device_size = '512MB'

    # 8x8 configuration, 8 devices each with an 8-bit interface
    device_bus_width = 8

    # DDR4 is a BL8 device
    burst_length = 8

    # Each device has a page (row buffer) size of 1 Kbyte (1K columns x8)
    device_rowbuffer_size = '1kB'

    # 8x8 configuration, so 8 devices
    devices_per_rank = 8

    # Match our DDR3 configurations which is dual rank
    ranks_per_channel = 2

    # DDR4 has 2 (x16) or 4 (x4 and x8) bank groups
    # Set to 4 for x4, x8 case
    bank_groups_per_rank = 4

    # DDR4 has 16 banks (4 bank groups) in all
    # configurations. Currently we do not capture the additional
    # constraints incurred by the bank groups
    banks_per_rank = 16

    # 1200 MHz
    tCK = '0.833ns'

    # 8 beats across an x64 interface translates to 4 clocks @ 1200 MHz
    # tBURST is equivalent to the CAS-to-CAS delay (tCCD)
    # With bank group architectures, tBURST represents the CAS-to-CAS
    # delay for bursts to different bank groups (tCCD_S)
    tBURST = '3.333ns'

    # @2400 data rate, tCCD_L is 6 CK
    # CAS-to-CAS delay for bursts to the same bank group
    # tBURST is equivalent to tCCD_S; no explicit parameter required
    # for CAS-to-CAS delay for bursts to different bank groups
    tCCD_L = '5ns';

    # DDR4-2400 17-17-17
    tRCD = '14.16ns'
    tCL = '14.16ns'
    tRP = '14.16ns'
    tRAS = '32ns'

    # RRD_S (different bank group) for 1K page is MAX(4 CK, 3.3ns)
    tRRD = '3.3ns'

    # RRD_L (same bank group) for 1K page is MAX(4 CK, 4.9ns)
    tRRD_L = '4.9ns';

    tXAW = '21ns'
    activation_limit = 4
    tRFC = '350ns'

    tWR = '15ns'

    # Here using the average of WTR_S and WTR_L
    tWTR = '5ns'

    # Greater of 4 CK or 7.5 ns
    tRTP = '7.5ns'

    # Default same rank rd-to-wr bus turnaround to 2 CK, @1200 MHz = 1.666 ns
    tRTW = '1.666ns'

    # Default different rank bus delay to 2 CK, @1200 MHz = 1.666 ns
    tCS = '1.666ns'

    # <=85C, half for >85C
    tREFI = '7.8us'

    # Current values from datasheet
    IDD0 = '64mA'
    IDD02 = '4mA'
    IDD2N = '50mA'
    IDD3N = '67mA'
    IDD3N2 = '3mA'
    IDD4W = '180mA'
    IDD4R = '160mA'
    IDD5 = '192mA'
    VDD = '1.2V'
    VDD2 = '2.5V'

# A single LPDDR2-S4 x32 interface (one command/address bus), with
# default timings based on a LPDDR2-1066 4 Gbit part (Micron MT42L128M32D1)
# in a 1x32 configuration.
class LPDDR2_S4_1066_x32(DRAMCtrl):
    # No DLL in LPDDR2
    dll = False

    # size of device
    device_size = '512MB'

    # 1x32 configuration, 1 device with a 32-bit interface
    device_bus_width = 32

    # LPDDR2_S4 is a BL4 and BL8 device
    burst_length = 8

    # Each device has a page (row buffer) size of 1KB
    # (this depends on the memory density)
    device_rowbuffer_size = '1kB'

    # 1x32 configuration, so 1 device
    devices_per_rank = 1

    # Use a single rank
    ranks_per_channel = 1

    # LPDDR2-S4 has 8 banks in all configurations
    banks_per_rank = 8

    # 533 MHz
    tCK = '1.876ns'

    # Fixed at 15 ns
    tRCD = '15ns'

    # 8 CK read latency, 4 CK write latency @ 533 MHz, 1.876 ns cycle time
    tCL = '15ns'

    # Pre-charge one bank 15 ns (all banks 18 ns)
    tRP = '15ns'

    tRAS = '42ns'
    tWR = '15ns'

    tRTP = '7.5ns'

    # 8 beats across an x32 DDR interface translates to 4 clocks @ 533 MHz.
    # Note this is a BL8 DDR device.
    # Requests larger than 32 bytes are broken down into multiple requests
    # in the controller
    tBURST = '7.5ns'

    # LPDDR2-S4, 4 Gbit
    tRFC = '130ns'
    tREFI = '3.9us'

    # Irrespective of speed grade, tWTR is 7.5 ns
    tWTR = '7.5ns'

    # Default same rank rd-to-wr bus turnaround to 2 CK, @533 MHz = 3.75 ns
    tRTW = '3.75ns'

    # Default different rank bus delay to 2 CK, @533 MHz = 3.75 ns
    tCS = '3.75ns'

    # Activate to activate irrespective of density and speed grade
    tRRD = '10.0ns'

    # Irrespective of density, tFAW is 50 ns
    tXAW = '50ns'
    activation_limit = 4

    # Current values from datasheet
    IDD0 = '15mA'
    IDD02 = '70mA'
    IDD2N = '2mA'
    IDD2N2 = '30mA'
    IDD3N = '2.5mA'
    IDD3N2 = '30mA'
    IDD4W = '10mA'
    IDD4W2 = '190mA'
    IDD4R = '3mA'
    IDD4R2 = '220mA'
    IDD5 = '40mA'
    IDD52 = '150mA'
    VDD = '1.8V'
    VDD2 = '1.2V'

# A single WideIO x128 interface (one command and address bus), with
# default timings based on an estimated WIO-200 8 Gbit part.
class WideIO_200_x128(DRAMCtrl):
    # No DLL for WideIO
    dll = False

    # size of device
    device_size = '1024MB'

    # 1x128 configuration, 1 device with a 128-bit interface
    device_bus_width = 128

    # This is a BL4 device
    burst_length = 4

    # Each device has a page (row buffer) size of 4KB
    # (this depends on the memory density)
    device_rowbuffer_size = '4kB'

    # 1x128 configuration, so 1 device
    devices_per_rank = 1

    # Use one rank for a one-high die stack
    ranks_per_channel = 1

    # WideIO has 4 banks in all configurations
    banks_per_rank = 4

    # 200 MHz
    tCK = '5ns'

    # WIO-200
    tRCD = '18ns'
    tCL = '18ns'
    tRP = '18ns'
    tRAS = '42ns'
    tWR = '15ns'
    # Read to precharge is same as the burst
    tRTP = '20ns'

    # 4 beats across an x128 SDR interface translates to 4 clocks @ 200 MHz.
    # Note this is a BL4 SDR device.
    tBURST = '20ns'

    # WIO 8 Gb
    tRFC = '210ns'

    # WIO 8 Gb, <=85C, half for >85C
    tREFI = '3.9us'

    # Greater of 2 CK or 15 ns, 2 CK @ 200 MHz = 10 ns
    tWTR = '15ns'

    # Default same rank rd-to-wr bus turnaround to 2 CK, @200 MHz = 10 ns
    tRTW = '10ns'

    # Default different rank bus delay to 2 CK, @200 MHz = 10 ns
    tCS = '10ns'

    # Activate to activate irrespective of density and speed grade
    tRRD = '10.0ns'

    # Two instead of four activation window
    tXAW = '50ns'
    activation_limit = 2

    # The WideIO specification does not provide current information

# A single LPDDR3 x32 interface (one command/address bus), with
# default timings based on a LPDDR3-1600 4 Gbit part (Micron
# EDF8132A1MC) in a 1x32 configuration.
class LPDDR3_1600_x32(DRAMCtrl):
    # No DLL for LPDDR3
    dll = False

    # size of device
    device_size = '512MB'

    # 1x32 configuration, 1 device with a 32-bit interface
    device_bus_width = 32

    # LPDDR3 is a BL8 device
    burst_length = 8

    # Each device has a page (row buffer) size of 4KB
    device_rowbuffer_size = '4kB'

    # 1x32 configuration, so 1 device
    devices_per_rank = 1

    # Technically the datasheet is a dual-rank package, but for
    # comparison with the LPDDR2 config we stick to a single rank
    ranks_per_channel = 1

    # LPDDR3 has 8 banks in all configurations
    banks_per_rank = 8

    # 800 MHz
    tCK = '1.25ns'

    tRCD = '18ns'

    # 12 CK read latency, 6 CK write latency @ 800 MHz, 1.25 ns cycle time
    tCL = '15ns'

    tRAS = '42ns'
    tWR = '15ns'

    # Greater of 4 CK or 7.5 ns, 4 CK @ 800 MHz = 5 ns
    tRTP = '7.5ns'

    # Pre-charge one bank 18 ns (all banks 21 ns)
    tRP = '18ns'

    # 8 beats across a x32 DDR interface translates to 4 clocks @ 800 MHz.
    # Note this is a BL8 DDR device.
    # Requests larger than 32 bytes are broken down into multiple requests
    # in the controller
    tBURST = '5ns'

    # LPDDR3, 4 Gb
    tRFC = '130ns'
    tREFI = '3.9us'

    # Irrespective of speed grade, tWTR is 7.5 ns
    tWTR = '7.5ns'

    # Default same rank rd-to-wr bus turnaround to 2 CK, @800 MHz = 2.5 ns
    tRTW = '2.5ns'

    # Default different rank bus delay to 2 CK, @800 MHz = 2.5 ns
    tCS = '2.5ns'

    # Activate to activate irrespective of density and speed grade
    tRRD = '10.0ns'

    # Irrespective of size, tFAW is 50 ns
    tXAW = '50ns'
    activation_limit = 4

    # Current values from datasheet
    IDD0 = '8mA'
    IDD02 = '60mA'
    IDD2N = '0.8mA'
    IDD2N2 = '26mA'
    IDD3N = '2mA'
    IDD3N2 = '34mA'
    IDD4W = '2mA'
    IDD4W2 = '190mA'
    IDD4R = '2mA'
    IDD4R2 = '230mA'
    IDD5 = '28mA'
    IDD52 = '150mA'
    VDD = '1.8V'
    VDD2 = '1.2V'

######################################################################################### Erfan
class HMCVault(DRAMCtrl):

    addr_mapping = 'RoCoRaBaCh'
	
    # size of device in bytes
    device_size = '32MB'

    # 8x8 configuration, 8 devices each with an 8-bit interface
    device_bus_width = 32

    # DDR3 is a BL8 device
    burst_length = 64

    # Row buffer size
    device_rowbuffer_size = '256B'

    # 8x8 configuration, so 8 devices
    devices_per_rank = 1

    # Because we have four stacked layers by default
    ranks_per_channel = 4

    # HMC has two banks per vault per layer
    banks_per_rank = 2
    
    page_policy = 'close'

    # 800 MHz
    tCK = '0.8ns'

    # 8 beats across an x64 interface translates to 4 clocks @ 800 MHz
    tBURST = '25.6ns'

    # DDR3-1600 11-11-11
    tRCD = '13.75ns'
    tCL = '13.75ns'
    tRP = '13.75ns'
    tRAS = '27.5ns'
    tRRD = '2.8ns'
    tXAW = '30ns'
    activation_limit = 0
    tRFC = '84.6ns'

    tWR = '15ns'

    # Greater of 4 CK or 7.5 ns
    tWTR = '7.5ns'

    # Greater of 4 CK or 7.5 ns
    tRTP = '7.5ns'

    # Default same rank rd-to-wr bus turnaround to 2 CK, @800 MHz = 2.5 ns
    tRTW = '2.5ns'

    # Default different rank bus delay to 2 CK, @800 MHz = 2.5 ns
    tCS = '2.5ns'

    # <=85C, half for >85C
    tREFI = '3.9us'

    # Current values from datasheet
    IDD0 = '75mA'
    IDD2N = '50mA'
    IDD3N = '57mA'
    IDD4W = '165mA'
    IDD4R = '187mA'
    IDD5 = '220mA'
    VDD = '1.2V'            # Brent Keeth - HMC - 2012

######################################################################################### Erfan
