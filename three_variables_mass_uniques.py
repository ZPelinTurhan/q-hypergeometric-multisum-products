import math
import time
import numpy as np

def multiply_three(list_a, list_b, list_c, max_len):
    """Efficiently convolve three lists using NumPy."""
    res = np.convolve(list_a, list_b)
    res = np.convolve(res, list_c)
    return res[:max_len].tolist()

def compute_three_variable_q_series(params, S):
    # Unpack parameters: A-F are quadratic, G-I are cross-terms, J-L are linear, k,L,M are steps
    A, B, C, D, E, F, G, H, I, J, K_step, L_step, M_step = params
    #print(f"Parameters: A={A}, B={B}, C={C}, D={D}, E={E}, F={F}, G={G}, H={H}, I={I}, J={J}, K_step={K_step}, L_step={L_step}, M_step={M_step}")
    def quadratic_form(m, n, r):
        # Full 3-variable quadratic form
        val = A*m*(m+1)//2 + B*n*(n+1)//2 + C*r*(r+1)//2
        val += D*m*n + E*m*r + F*n*r
        val += G*m + H*n + I*r + J
        return val

    coefficients = [0] * (S + 1)
    memo = [{} for _ in range(3)] # memo_m, memo_n, memo_r

    def get_gf(val, step, memo_idx):
        if val in memo[memo_idx]: return memo[memo_idx][val]
        arr = [0] * (S + 1)
        arr[0] = 1
        limit, p = val * step, step
        while p <= limit and p <= S:
            for j in range(p, S + 1):
                arr[j] += arr[j - p]
            p += step
        memo[memo_idx][val] = arr
        return arr

    m = 0
    while True:
        Qm = quadratic_form(m, 0, 0)
        if Qm > S: break
        n = 0
        while True:
            Qmn = quadratic_form(m, n, 0)
            if Qmn > S: break
            r = 0
            while True:
                Qmnr = quadratic_form(m, n, r)
                if Qmnr > S: break
                
                # Exponent space remaining
                tail = S - Qmnr
                gf_m = get_gf(m, K_step, 0)[:tail+1]
                gf_n = get_gf(n, L_step, 1)[:tail+1]
                gf_r = get_gf(r, M_step, 2)[:tail+1]

                # Combine the three generating functions
                combined = multiply_three(gf_m, gf_n, gf_r, tail + 1)

                # Add to main coefficients
                for t, val in enumerate(combined):
                    if Qmnr + t <= S and Qmnr + t >= 0:
                        coefficients[Qmnr + t] += val
                r += 1
            n += 1
        m += 1
    return coefficients

def sum_to_product(sum_coeffs, S):
    # sum_coeffs: a_n from A(q) = Σ a_n q^n
    # returns b_n from A(q) = Π (1 - q^n)^{-b_n}
    if not sum_coeffs or sum_coeffs[0] == 0:
        return [0] * (S + 1)
        
    # We use the identity: n * a_n = Σ_{k=1}^n c_k * a_{n-k}
    # where c_k = Σ_{d|k} d * b_d
    c = [0] * (S + 1)
    b = [0] * (S + 1)
    
    for n in range(1, S + 1):
        # Calculate n * a_n
        rhs = n * sum_coeffs[n]
        # Subtract the convolution part
        internal_sum = 0
        for k in range(1, n):
            internal_sum += c[k] * sum_coeffs[n - k]
        
        c[n] = rhs - internal_sum
        
        # Mobius Inversion or simpler: b_n = (c_n - Σ_{d|n, d<n} d * b_d) / n
        b_sum = 0
        for d in range(1, n):
            if n % d == 0:
                b_sum += d * b[d]
        b[n] = (c[n] - b_sum) // n
        
    return b

def test_periodicity(arr, min_period=1):
    offset = len(arr) // 8 + 1
    data = arr[offset:]
    n = len(data)
    
    for p in range(min_period, n // 2 + 1):
        pattern = data[:p]
        if all(data[i] == pattern[i % p] for i in range(n)):
            return p
    return None

def compute_product_coefficients_with_periodicity(params, S):
    sum_coefficients = compute_three_variable_q_series(params, S)
    prod_coefficients = sum_to_product(sum_coefficients, S)
    if prod_coefficients == "ERROR":
        return "ERROR"
    
    period = test_periodicity(prod_coefficients)
    if period:
        print(f"Periodicity detected with period {period}")
    else:
        print("No periodicity detected")
    
    return prod_coefficients

def compute_series_mass( A_max=1 ,B_max=1 , C_max=1 , k=1 , l=1 , m=1 , S=10):
    if A_max <= 0 or B_max <= 0 or C_max <= 0 or k <= 0 or l <= 0 or m <= 0 or S <= 0:
        return "ERROR"
    g=open(f"./results/product_series_for_{A_max}_{B_max}_{C_max}_{k}_{l}_{m}_{S}_uniques.txt","w")
    g.write(f"Computing product coefficients for A_max = {A_max}, B_max = {B_max}, C_max = {C_max}, k = {k}, l = {l}, m = {m}, S = {S}\n\n")
    start_time = time.time()
    count=0
    seen_series = set()
    for A in range (1, A_max + 1):
        B_min = A if (k == l and A <= B_max) else 1
        for B in range (B_min, B_max + 1):
            if l==m and B <= C_max:
                C_min= B
            elif k==m and A <= C_max:
                C_min=A
            else:
                C_min=1
                
            for C in range (C_min   , C_max + 1):
                print(f"Calculating for A = {A}, B = {B}, C = {C}")
                D_range = math.floor((A * B)**0.5)
                E_range = math.floor((A * C)**0.5)
                F_range = math.floor((B * C)**0.5)
                G_range = math.floor(A/2)
                H_range = math.floor(B/2)
                I_range = math.floor(C/2)
                count += (2*D_range)*(2*E_range)*(2*F_range)
                for D in range(-D_range,D_range+1):
                    for E in range(-E_range,E_range+1):
                        for F in range(-F_range,F_range+1):
                            for G in range(-G_range,G_range+1):
                                for H in range(-H_range,H_range+1):
                                    for I in range(-I_range,I_range+1):
                                        coeffs = compute_three_variable_q_series((A, B, C, D, E, F, G, H, I, 0, k, l, m), S)
                                        if coeffs == "ERROR":
                                            print(f"Errored for inputs {[A,B,C,D,E,F,G,H,I,0,k,l,m,S]}")
                                            return "ERROR"
                                        count+=1
                                        prod_coeffs = sum_to_product(coeffs,S)
                                        periodicity = test_periodicity(prod_coeffs)
                                        if periodicity is not None:
                                            signature = tuple(prod_coeffs)
                                            if signature not in seen_series:
                                                seen_series.add(signature)
                                                print(f"Periodicity detected for inputs {[A,B,C,D,E,F,G,H,I,0,k,l,m,S]} with period {periodicity}")
                                                g.write(f"{[A,B,C,D,E,F,G,H,I,0,k,l,m,S]}, period = {periodicity}\t")
                                                g.write(f"{prod_coeffs}\n")
    end_time = time.time()
    elapsed = end_time - start_time
    g.write(f"\nCalculated {count} series of length {S} in {format(elapsed)} seconds")
    g.close()

if __name__ == "__main__":
    output = compute_series_mass( 3 , 2 , 2 , 2 , 2 , 1 , 30) # A_max, B_max, C_max, k, l, m, S
    #A*c(m+1,2)+B*c(n+1,2)+C*c(r+1,2)+D*m*n+E*m*r+F*n*r+G*m+H*n+I*r+J, k_step: m's step, l_step: n's step, m_step: r's step
    #Number of series for A=B=C=n: c(2n+3,3)*(2*floor(n/2)+1)^3
    if output == "ERROR":
        print("Incorrect inputs")
    else:
        print(f"Computation complete")