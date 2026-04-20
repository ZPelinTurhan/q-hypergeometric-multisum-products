import math
import time
import os
import numpy as np
# Σ(m,n≥0) q^(A·m(m+1)/2 + B·m·n + C·n(n+1)/2 + D·m + E·n + F) / ((q^k; q^k)_m · (q^L; q^L)_n)

# multiply two coefficient lists
# list_a -> A(q) = ∑ a_i q^i
# list_b -> B(q) = ∑ b_j q^j
# C(q) = A(q) * B(q) -> c_k = sum of (a_i * b_j) over all i and j such that i + j = k

def multiply(list_a, list_b, max_len=None):
    # Using 'full' returns the standard convolution
    result = np.convolve(list_a, list_b)
    if max_len is not None:
        return result[:max_len].tolist()
    return result.tolist()

def compute_two_variable_q_series(A, B, C, D, E, F, k, L, S):
    
    if k < 1:
        print("Step size k must be at least 1")
        return "ERROR"
    if L < 1:
        print("Step size L must be at least 1")
        return "ERROR"
    if S < 0:
        print("Highest exponent must be at least 0")
        return "ERROR"
    if F < 0:
        print("Constant term F must be non-negative")
        return "ERROR"
    if A <= 0 or C <= 0:
        print("Coefficient of squares (A and C) must be positive")
        return "ERROR"
    
    def quadratic_form(m, n):
        value = A * m * (m + 1) // 2
        value += B * m * n
        value += C * n * (n + 1) // 2
        value += D * m
        value += E * n
        value += F
        
        if value < 0:
            print("Polinomial must not go into the negative")
            print(f"For inputs {m} , {n}")
            return "ERROR"
        
        return value

    # create the coefficient list c_0 through c_S
    coefficients = [0] * (S + 1)

    if S == 0:
        q0 = quadratic_form(0, 0)
        
        if q0 == "ERROR":
            return "ERROR"
        
        if q0 == 0:
            coefficients[0] = 1
        return coefficients

    memo_m = {}
    memo_n = {}

    # build the generating function for 1/(q^k;q^k)_m
    def gf_m_func(m):
        if m in memo_m:
            return memo_m[m]

        arr = [0] * (S + 1)
        arr[0] = 1

        largest_part = m * k
        part = k

        # build the generating function using standard partition recurrence
        while part <= largest_part and part <= S:
            j = part
            while j <= S:
                arr[j] += arr[j - part]
                j += 1
            part += k

        memo_m[m] = arr
        return arr

    # build the generating function for 1/(q^L;q^L)_n
    def gf_n_func(n):
        if n in memo_n:
            return memo_n[n]

        arr = [0] * (S + 1)
        arr[0] = 1

        largest_part = n * L
        part = L

        # build the generating function using the same partition logic
        while part <= largest_part and part <= S:
            j = part
            while j <= S:
                arr[j] += arr[j - part]
                j += 1
            part += L

        memo_n[n] = arr
        return arr
    
    for m in range(S + 1):
        for n in range(S + 1):
            Qmn = quadratic_form(m, n)
            if Qmn < 0 or Qmn > S:
                continue
            q_val = Qmn
            if q_val <= S:
                # compute how much exponent space is left
                tail = S - q_val
                full_gf_m = gf_m_func(m)
                full_gf_n = gf_n_func(n)

                # cut the lists to the usable part (0 to tail)
                sub_m = full_gf_m[:tail + 1]
                sub_n = full_gf_n[:tail + 1]

                product_list = multiply(sub_m, sub_n, max_len=tail + 1)

                # shift by q_val and add into the total coefficients
                t = 0
                while t < len(product_list):
                    idx = q_val + t
                    if idx <= S:
                        coefficients[idx] += product_list[t]
                    t += 1

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

def compute_series_mass( A_max=1 , C_max=1 , k=1 , l=1 , S=10):
    if A_max <= 0 or C_max <= 0 or k <= 0 or l <= 0 or S <= 0:
        return "ERROR"
    g=open(f"product_series_for_{A_max}_{C_max}_{k}_{l}_{S}.txt","w")
    g.write(f"Computing product coefficients for A_max = {A_max}, C_max = {C_max}, k = {k}, l = {l}, S = {S}\n\n")
    start_time = time.time()
    for A in range (1, A_max + 1):
        for C in range (1, C_max + 1):
            print(f"Calculating for A = {A}, C = {C}")
            b_range = math.floor((A * C)**0.5)
            d_range = math.floor(A/2)
            e_range = math.floor(C/2)
            count = (2*b_range)*(2*d_range)*(2*e_range)
            for B in range(-b_range,b_range):
                for D in range(-d_range,d_range):
                    for E in range(-e_range,e_range):
                        F = 0
                        coeffs = compute_two_variable_q_series(A, B, C, D, E, F, k, l, S)
                        if coeffs == "ERROR":
                            print(f"Errored for inputs {[A,B,C,D,E,0,k,l,S]}")
                            return "ERROR"
                        prod_coeffs = sum_to_product(coeffs,S)
                        periodicity = test_periodicity(prod_coeffs)
                        if periodicity is not None:
                            print(f"Periodicity detected for inputs {[A,B,C,D,E,0,k,l,S]} with period {periodicity}")
                            g.write(f"{[A,B,C,D,E,0,k,l,S]}, period = {periodicity}\t")
                            g.write(f"{prod_coeffs}\n")

    end_time = time.time()
    elapsed = end_time - start_time
    g.write(f"\nCalculated {count} series of length {S} in {format(elapsed)} seconds")
    g.close()
    return "COMPLETE"

def test_periodicity(arr):

    def test_periodicity(arr, k):
        # check if arr is periodic with period k
        for i in range(len(arr) - k):
            if arr[i] != arr[i + k]:
                return False
        return True
    
    for k in range(2 , len(arr) // 2 + 1):
            if test_periodicity(arr, k):
                return k
    return None

if __name__ == "__main__":

    output = compute_series_mass( 12 , 12 , 1 , 1 , 25) # A_max, C_max, k, l, S 
    #will calculate for 1 <= A <= A_max , 1 <= C <= C_max, 
    # B^2 < A*C, -A/2 < D < A/2 , -C/2 < E < C/2, F = 0

    if output == "ERROR":
        print("Incorrect inputs")
    else:
        print(f"Computation complete")