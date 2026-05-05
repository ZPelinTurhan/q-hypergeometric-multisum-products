# Finding Product Representations of q-Hypergeometric Multisums

## Group Members

* Zeynep Pelin Turhan
* Muhammed Akgöçmen

## Project Description

This project implements a system for computing Maclaurin coefficients of q-hypergeometric multisums of the form

$$\sum_{m,n,r \ge 0} \frac{q^{Am(m+1)/2 + Bn(n+1)/2 + Cr(r+1)/2 + Dmn + Emr + Fnr + Gm + Hn + Ir + J}}{(q^k;q^k)_m \, (q^L;q^L)_n \, (q^M;q^M)_r}$$

The system first computes the Maclaurin coefficients of the multisum and derives the corresponding product coefficients. The resulting product sequences are then analyzed for periodic behavior, which may indicate an underlying product structure.

## Project Goal

The goal of this project is to:

* Compute Maclaurin coefficients of q-hypergeometric multisums efficiently
* Detect periodicity in coefficient sequences
* Use this periodicity to identify potential product representations
* Provide a user-friendly interface to experiment with different parameters

## Implementation

The system is implemented using:

* Python for computation
* Flask for the web interface

The application allows users to:

* Input parameters of a multisum
* Compute sum coefficients
* Compute product coefficients
* Detect periodicity
* Download results in TXT, CSV, and JSON formats

## Extension to Three Variables

The initial implementation supported **second-degree (two-variable) multisums**.
In this version, the system has been extended to support **three-variable multisums**.

This required:

* Modifying the exponent structure to include an additional summation variable
* Extending the coefficient computation algorithm
* Updating the interface to handle additional parameters

This extension allows the system to explore more complex combinatorial structures and broader classes of q-series.

## Notes

* The system uses exact integer arithmetic and memoization for efficiency
* It is designed as an academic tool for experimentation and exploration
* Results can vary depending on input parameters and may not always yield product representations
