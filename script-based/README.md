# DNS Magnitude calculation - script-based implementation

This directory contains the script-based (lossless) implementation to calculate DNS Magnitude of the L-Root server based on the "royparse" format style files. 

While these scripts are not optimized in any way, their simplicity creates ground truth for benchmarking / verifying more sophisticated and/or optimized implementations.

The software is solely based on shell / awk scripts

## Usage

To calculate the DNS Magnitude for a certain set of source files, the following steps need to be performed. Note that contrary to the `hll-based` approach, results of various runs cannot be merded, so all data to be included in the result has to be available for each of the steps.

For example, to calculate a list with top20 TLDs sorted by DNS Magnitude for a specific file. Note what while the input file has a ".cbor" suffix, it is actually expected to be a text file in "royparse" format.

```bash
export TOTALHOSTS=`cat rp.20180501-183420_300.cbor | ./get_total_uniq_hosts.sh`
cat rp.20180501-183420_300.cbor | ./calc-mag.sh   | head -20
```

To caclulate the DNS magnitude for a whole day (input and output paths have to be set at the top of the script):

```bash
./calc-mag-day-royparse.sh YYYYMMDD
``` 

## Description of Individual scripts

  * **get_total_uniq_hosts.sh**: Returns the total number of unique hosts, based on "new format" files as STDIN
  * **get_tld_counters.sh**: Returns the number unique request per TLD for the files given on STDIN. Used indirectly via calc_mag.sh
  * **calc-mag.sh**: Calculates DNS Magnitude for the "new format" data given on STDIN, based on $TOTALHOSTS given via environment. See above for example of how to use this script
  * **get_unique_tlds_per_file.sh**: Creates a list of TLDs which occur in royparse files in given directories. Start directory is hardcoded in script - beware!
  * **calc-mag-day-royparse.sh**: Takes a YYYYMMDD-data as argument and calculates the magnitude for the given day. Configuration is done on top of the script. This script reads royparse files and generates 2 output files:
    * **YYYYMMDD.mags**: CSV file with header "date,tld,magnitude,uniquehosts". Contains the date, tld, calculated magnitude and the number of uniques hosts for this tld. Order by magnitude descending. The file also includes a line with the "fake" TLD "TOTALUNIQUEHOSTS" containing the total number of unique IP addresses.
    * **YYYYMMDD.querycounts**: CSV file with header "date,tld,querycount". Contains the date,tld and the total number of queries for this tld. Ordered by number of queries descending.
    * **YYYYMMDD.total**: Contains a single line with the total number of unique clients observed during the day
  * **aggregate_ip.py**: Reads "royparse" files from STDIN, aggregates the IP adresses to /24 (IPv4) or /48 (IPv6) and write it in the "royparse" format to STDOUT.

**NOTE**: This scripts are optimized for servers with 64GB of memory. Servers with less than 64GB memory may run out of memory and the script will be killed be the operating system's out-of-memory killer, which can lead to incomplete processing. To avoid this the memory usage parameters of the sort commands (e.g. -S 24G) in the script must be changed accordingly.

A good indication of incomplete processing is a missing "TOTALUNIQUEHOSTS" fake TLD in a resulting DNS Magnitude list.

### Sample Usecase

Loop through all days in a directory and calculated the magnitude, starting from the latest day back to the past.

```bash
for d in `find /data/curated/* -maxdepth 0  -type d  -printf "%f\n"  | sort -r`; do
    echo "Processing $d"
    time ./calc-mag-day-magnitude-format.sh $d
done

```

