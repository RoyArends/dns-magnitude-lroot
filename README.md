# DNS Magnitude calculation from L-Root (IMRS) data

Michael Braunöder <michael.braunoeder@nic.at> - Alexander Mayrhofer <alexander.mayrhofer@nic.at>

The software contained in this repository was developed to calculate DNS Magnitude values from traffic data of the ICANN Managed Root Server (IMRS, also known as "L-Root") on a per-TLD basis.

DNS Magnitude is a logarithmic measure for the DNS popularity of a domain name, based on counting unique client addresses, normalized to the 0-10 range.

## Software Variants

The calculation software exists in two variants, one developed using shell scripting techniques (see `script-based` directory), and one developed in Python, using HyperLogLog (HLL) probabilistic data structures (see `hll-based` directory). The reason for this is that initially, we expected to encounter a massive number of unique IP addresses, and a limited number of TLDs, where an HLL-based approach would have been more advantegous. However, in practice, the number of unique client IP addresses is surprisingly low, while the number of TLDs is massive. This property makes a precise, script-based approach feasible.

HLLs are probabilistic, therefore a certain margin of error is introduced in calculations. On the other hand, the script-based approach does not introduce any margin of error, because it does not make use of a probabilistic data structure. 

For the use case of calculating the DNS Magnitude of TLDs based on root-level traffic, the `script-based` software is therefore recommended.

More information on the two variants is found in the `README` of the respective subdirectories.

Licensing information can be found in `LICENSE`, changes are tracked in `CHANGES`

