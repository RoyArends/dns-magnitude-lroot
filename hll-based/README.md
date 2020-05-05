# DNS Magnitude calcuation for L-root traffic

Michael Braunoeder <michael.braunoeder@nic.at> - Alex Mayrhofer <alexander.mayrhofer@nic.at>

## Overview

The software in this directory calculates DNS Magnitude values for TLDs, based on "royparse" format files of traffic from the L-root servers. The same software might be used on other formats with slight modifications of the input processing.

As DNS Magnitude requires counting of unique values (cardinality) of IP addresses, the calculation is quite memory-intensive. Particularly because aggregations that involve counts of unique values can not be "merged" by a simple addition of sub-components, but require a set operation. 

For a high number of unique client IP addresses, the software in this directory provides an implementation that allows for better parallelization than a "full" algorithm, for the sacrifice of slight losses in precision and result extent. Specifically, the optimizations used in this software are as follows:

  * A "whitelist" is used to filter TLDs to a sensible subset (where only the subset is considered from DNS Magnitude calculation)
  * HyperLogLog data structures are used to perform (a) memory-efficient counting/estimation of unique IP addresses and (b) efficient merging of results from subsets of data

Note that a lossless alternative implementation is provided in `../script-based`, which can be used to benchmark results from this HLL-based implementation.

## Motivation for "whitelist" and HLL-based counting

The initial expectations with regards to data from the L-root servers were that the data set would contain a fairly limited number of TLDs, but a massive number of IP addresses, even for individual files. It turned out that the contrary is true - the available set of traffic snapshots (spanning about 10 minutes) contains almost 41 millions of unique Top Level Domains, but only about 500k unique IP addresses.

Most of those 41 million TLDs occur very infrequently, or would not qualify as a valid top level domain anyways. Reducing the number of TLDs for which DNS magnitude is calculated to the sensible subset of "most popular" TLDs greatly reduces the effort required. This is the motivation to "whitelist" the TLDs before performing calculation.

The source data set is split into many small "fragments", and as explained above, calculation of DNS magnitude requires set operations across the unique IP addresses when results from those fragments are merged. HyperLogLogs are data structures which are specifically optimized to estimate the cardinaility of a data set, and support set-operation style merging. Therefore, HLLs are used as a intermediate step. This intermediate step is completely self-contained "per fragment", and hence can be performed in parallel on multiple fragments.

The basic workflow / architecture of calculating TLD Magnitude for TLDs is therefore as follows:

  * Create a "whitelist"
  * Create HLL structures on data filtered by "whitelist"
  * Merge HLLs across the desired extent of data
  * Calculate DNS magnitude based on cardinalities extracted from HLLs

The individual steps are described below

## Calculating DNS Magnitude for the given 10 minute data set

### Create "whitelist"

For the current set of data, a simple approach for creating the whitelist is followed. Only **TLDs which occur in more than one file** are considered for calculation. The first step creates one list of TLDs per file:

```bash
cd ../script-based
./get_unique_tlds_per_file.sh
```

This creates Files with the suffix `.unique_tlds` for each of the input data files. Those files can then be rolled into a single "whitelist" python object as follows:

```bash
cd ../hll-based
 cat ../script-based/data/curated/20190601/*/*.unique_tlds | sort | uniq -c   > tldtoplist.tld
 cat tldtoplist.tld  | ./make_whitelist_object.py -l 1 -o whitelist.pickle
```

The make_whitelist_object.py script supports the following parameters:

  * `-o <path>`: Path of the output file to be written
  * `-l <number>`: Limit TLDs to those occuring in more than `<number>` files

(runtime approx. 3m40s for the first step, about 1m8 for the second step, about  23s for the third step. Note that the first step can be performed in parallel on the files, while the second step requires all TLD lists from each file to be present)

### HyperLogLog structure, creation & merging

HyperLogLogs are probabilistic data structures to estimate the cardinality of a data set. As calculation of DNS magnitude must be done for each TLD, one HLL per TLD is required. The script uses an SQLite database to store the collection of HLLs for each input file, and compresses the HLLs on storage for disk efficiency. 

HLLs are then independent of the source "royparse" file, and can eg. be kept if the original data is removed, providing an archive of DNS magnitude source information. Note that the if aggregation / exclusion of IP protocol families is performed, this requires a complete, seperate set of HLL collection files.

A HLL collection for a certain file is created as follows:

```bash
 ./royparse_to_hll.py -i ../script-based/data/curated/20190601/aa01-in-bom.l.dns.icann.org/rp.20190601-120350_300.cbor  --whitelist whitelist.pickle  --hlloutputfile 'bom.hll'
```

The script accepts the following parameters:

  * `-i <path>` or `--inputfile <path>` (required): Path of the royparse input file
  * `--whitelist <path>` (optional): Limit the creation of HLLs to the TLDs contained in the given "whitelist" pickle file located in `<path>` (see above for creation)
  * `--hlloutputfile <path>` (required): File name of the HLL collection output file
  * `--aggregate` (optional): If given, aggregate IP addresses to /24 (IPv4) or /48, respectively (IPv6)
  * `--ipv4only` (optional): consider IPv4 addresses only
  * `--ipv6only` (optional): consider IPv6 addresses only

Note that the script also creates a HLL for a "fake" TLD called "TOTALS" which contains the estimated total number of unique IP addresses in a file. (Since TLDs are always lowercased in the royparse format, this should not collide with requests for a potential literal "total" TLD)

Multiple HLL collections can then be merged using the following command. Note that merging can also be performed hierarchically, for example first for all files from a certain node, and subsequently merge those collections into a total across a full day.

```bash
./merge_hlls.py -o thisday.hll *.hll
```

merge_hlls.py supports the following command line options:

  * `-o` (required): Output file of HLL collection
  * `-r` (optional): "Reset" output HLL file, if it exists already. If not given, information from the source HLLs will be "merged" into the existing output HLL

### Calculation of DNS Magnitude

Finally, the DNS magnitude of a certain HLL collection file is calculated using the following script:

```bash
# calculate DNS magnitude (and sort by magnitude, descending)
./calculate-magnitude.py -f thisday.hll  |  sort -r -n -t';' -k 2
```

calculate_magnitude.py supports the following command line parameters/options:

  * `-f` (required): Input HLL collection file


## Calculating DNS Magnitude at scale (for a whole day)
### Create "whitelist" at scale

Due to the high number of files per day, the high number of traffic and the very big number of different queried TLDs  the above approach does not scale if you want to generate a whitelist based on the queries for a day). Limiting the number of TLDs to **TLDs which occur in more than one file** leads to a to high number of TLDs so the HLL generation afterwards does not scale. So the new approach is **TLDs which occur in more than 30 files in a day** which result in a whitelist with about 250k to 300k TLDs.

To generate the whitelists use the scripts:
  * **make_whitelists_parallel_royparse.sh**


### Create Hyperloglogs at scale

To generate the HLLs at scale the Unix approach "use small tools and chain them with pipes" has been choosen.

**NOTE**: The inputformat for these scripts are "new format" files. If royparse files should be processed please use the 'royparse2nf' script from the "script-based" directory.

The "royparse_to_hll.py" script has been split into two parts
  * **filter_whitelist.py** Reads "new format" files from STDIN and checks if TLD in provided whitelist. If yes IP and TLD is write to STDOUT, if not the line is dropped.
    
    The script accepts the following parameters:
    * `--whitelist <path>` (required): Whitelist object generated as described above.
  
  * **generate_hll.py** This scripts reads "new format" files from STDIN, aggregates the query source ip addresses (if wanted), adds them to a HLL per TLD and stores the HLL in the filesystem.

    The script accepts the following parameters:

    * `--hlloutputfile <path>` (required): File name of the HLL collection output file
    * `--aggregate` (optional): If given, aggregate IP addresses to /24 (IPv4) or /48, respectively (IPv6)
    * `--ipv4only` (optional): consider IPv4 addresses only
    * `--ipv6only` (optional): consider IPv6 addresses only

A sample workflow to generate the HLL for a give day might be 
```bash
 find /data/curated/20190307*/ -type f | parallel -j 10 zcat  | parallel -j 5  --block-size 1900M --pipe "./filter_whitelist.py --whitelist processed/whitelists/20190307-whitelist.pickle  | LANG=C sort  -S 2G --parallel=8 -u" | LANG=c  sort -S 2G --parallel=8 -u |  ./generate_hll.py --hlloutputfile processed/hlls/20190307.hll
```
