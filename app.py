from flask import Flask, render_template, request, send_file

from three_variables_mass_uniques import (
    compute_three_variable_q_series,
    sum_to_product,
    test_periodicity
)

from product_coefficients_with_periodicity import (
    compute_two_variable_q_series
)

import csv
import json
import uuid
import os
import tempfile
import time
import threading

app = Flask(__name__, template_folder='templates')

# define temp directory for storing results
RESULTS_DIR = os.path.join(tempfile.gettempdir(), "ens492_results")
# create directory if it does not exist
os.makedirs(RESULTS_DIR, exist_ok=True)

# how long to keep result files before cleanup (seconds)
RESULT_TTL = 3600
def cleanup_old_files():
    # remove result files older than RESULT_TTL
    while True:
        # wait 60 seconds between checks
        time.sleep(60)

        now = time.time()

        for fname in os.listdir(RESULTS_DIR):
            fpath = os.path.join(RESULTS_DIR, fname)
            try:
                # check if RESULT_TTL time has passed and remove if so
                if now - os.path.getmtime(fpath) > RESULT_TTL:
                    os.remove(fpath)
            except Exception:
                pass

# thread to cleanup in the background
threading.Thread(target=cleanup_old_files, daemon=True).start()

def save_three_variable_files(base, A, B, C, D, E, F, G_min, G_max,
                              H_min, H_max, I_min, I_max, J, k, L, M, S, all_results):

    # txt
    with open(f"{base}.txt", "w") as f:
        f.write("Parameters\n")
        f.write(
            f"A={A}, B={B}, C={C}, D={D}, E={E}, F={F}, "
            f"G_range=[{G_min},{G_max}], H_range=[{H_min},{H_max}], "
            f"I_range=[{I_min},{I_max}], J={J}, k={k}, L={L}, M={M}, S={S}\n\n"
        )

        f.write("Results\n\n")

        for res in all_results:
            f.write(f"G={res['G']}, H={res['H']}, I={res['I']}\n")
            f.write(f"Sum: {res['sum']}\n")
            f.write(f"Product: {res['prod']}\n")
            f.write(f"Period: {res['period']}\n\n")

    #csv
    with open(f"{base}.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(["sep=;"])

        writer.writerow(["Parameter", "Value"])
        writer.writerow(["A", A])
        writer.writerow(["B", B])
        writer.writerow(["C", C])

        writer.writerow(["D", D])
        writer.writerow(["E", E])
        writer.writerow(["F", F])

        writer.writerow(["G_min", G_min])
        writer.writerow(["G_max", G_max])

        writer.writerow(["H_min", H_min])
        writer.writerow(["H_max", H_max])

        writer.writerow(["I_min", I_min])
        writer.writerow(["I_max", I_max])

        writer.writerow(["J", J])
        writer.writerow(["k", k])
        writer.writerow(["L", L])
        writer.writerow(["M", M])
        writer.writerow(["S", S])

        writer.writerow([])
        writer.writerow(["G", "H", "I", "Index", "Sum_Coeff", "Product_Coeff"])

        for res in all_results:
            G = res["G"]
            H = res["H"]
            I = res["I"]

            for i, (sc, pc) in enumerate(zip(res["sum"], res["prod"])):
                writer.writerow([G, H, I, i, sc, pc])

    # json
    with open(f"{base}.json", "w") as f:
        json.dump({
            "parameters": {
                "A": A,
                "B": B,
                "C": C,

                "D": D,
                "E": E,
                "F": F,

                "G_range": [G_min, G_max],
                "H_range": [H_min, H_max],
                "I_range": [I_min, I_max],

                "J": J,
                "k": k,
                "L": L,
                "M": M,
                "S": S
            },
            "results": all_results
        }, f, indent=4)


@app.route("/")
def home():
    return render_template("home.html")

@app.route('/three-variable', methods=["GET", "POST"])
def three_variable():

    all_results = None
    result_id = None
    error = None

    if request.method == "POST":
        try:
            # get inputs from form and convert to int
            A = int(request.form["A"])
            B = int(request.form["B"])
            C = int(request.form["C"])
            D = int(request.form["D"])
            E = int(request.form["E"])

            G_min = int(request.form["G_min"])
            H_min = int(request.form["H_min"])
            I_min = int(request.form["I_min"])

            G_max_raw = request.form.get("G_max")
            H_max_raw = request.form.get("H_max")
            I_max_raw = request.form.get("I_max")

            if G_max_raw:
                G_max = int(G_max_raw)
            else:
                G_max = G_min

            if H_max_raw:
                H_max = int(H_max_raw)
            else:
                H_max = H_min

            if I_max_raw:
                I_max = int(I_max_raw)
            else:
                I_max = I_min

            F = int(request.form["F"])
            J = int(request.form["J"])
            k = int(request.form["k"])
            L = int(request.form["L"])
            M = int(request.form["M"])
            S = int(request.form["S"])

        except (KeyError, ValueError):
            # handle missing or invalid input
            error = "Invalid input: all parameters must be valid integers. Please check that every field contains a number."
            return render_template("three_variable.html", error=error)

        errors = []

        if G_min > G_max:
            errors.append("G_max cannot be smaller than G_min.")

        if H_min > H_max:
            errors.append("H_max cannot be smaller than H_min.")

        if I_min > I_max:
            errors.append("I_max cannot be smaller than I_min.")

        if errors:
            error = " ".join(errors)
            return render_template("three_variable.html", error=error)

        all_results = []

        for G in range(G_min, G_max + 1):
            for H in range(H_min, H_max + 1):
                for I in range(I_min, I_max + 1):

                    params = (A, B, C, D, E, F, G, H, I, J, k, L, M)

                    sum_coeffs = compute_three_variable_q_series(params, S)

                    if sum_coeffs == "ERROR":
                        continue

                    prod_coeffs = sum_to_product(sum_coeffs, S)
                    period = test_periodicity(prod_coeffs)

                    all_results.append({
                        "G": G,
                        "H": H,
                        "I": I,
                        "sum": sum_coeffs,
                        "prod": prod_coeffs,
                        "period": period
                    })

        # generate unique id for result
        result_id = str(uuid.uuid4())

        base = os.path.join(RESULTS_DIR, "three_" + result_id)

        save_three_variable_files(base, A, B, C, D, E, F, G_min, G_max,
                                  H_min, H_max, I_min, I_max, J, k, L, M, S, all_results)
        
    return render_template(
        "three_variable.html",
        all_results=all_results,
        result_id=result_id,
        error=error,
        params=request.form
    )


@app.route("/download/three-variable/<result_id>/<filetype>")
def download_three_variable(result_id, filetype):

    if filetype not in ("txt", "csv", "json"):
        return "Invalid file type", 400

    try:
        uuid.UUID(result_id)
        # validate uuid format
    except ValueError:
        return "Invalid result ID", 400

    filepath = os.path.join(RESULTS_DIR, f"three_{result_id}.{filetype}")

    if not os.path.exists(filepath):
        # check file exists
        return "Results not found", 404

    # send file to user for download
    return send_file(
        filepath,
        as_attachment=True,
        download_name=f"three_variable_results.{filetype}"
    )


def save_two_variable_files(base, A, B, C, D_min, D_max, 
                            E_min, E_max, F, k, L, S, all_results):

    # txt
    with open(f"{base}.txt", "w") as f:
        f.write("Parameters\n")
        f.write(
            f"A={A}, B={B}, C={C}, "
            f"D_range=[{D_min},{D_max}], "
            f"E_range=[{E_min},{E_max}], "
            f"F={F}, k={k}, L={L}, S={S}\n\n"
        )

        f.write("Results\n\n")

        for res in all_results:
            f.write(f"D={res['D']}, E={res['E']}\n")
            f.write(f"Sum: {res['sum']}\n")
            f.write(f"Product: {res['prod']}\n")
            f.write(f"Period: {res['period']}\n\n")

    #csv
    with open(f"{base}.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(["sep=;"])

        writer.writerow(["Parameter", "Value"])
        writer.writerow(["A", A])
        writer.writerow(["B", B])
        writer.writerow(["C", C])

        writer.writerow(["D_min", D_min])
        writer.writerow(["D_max", D_max])

        writer.writerow(["E_min", E_min])
        writer.writerow(["E_max", E_max])

        writer.writerow(["F", F])
        writer.writerow(["k", k])
        writer.writerow(["L", L])
        writer.writerow(["S", S])

        writer.writerow([])
        writer.writerow(["D", "E", "Index", "Sum_Coeff", "Product_Coeff"])

        for res in all_results:
            D = res["D"]
            E = res["E"]

            for i, (sc, pc) in enumerate(zip(res["sum"], res["prod"])):
                writer.writerow([D, E, i, sc, pc])

    # json
    with open(f"{base}.json", "w") as f:
        json.dump({
            "parameters": {
                "A": A,
                "B": B,
                "C": C,
                "D_range": [D_min, D_max],
                "E_range": [E_min, E_max],
                "F": F,
                "k": k,
                "L": L,
                "S": S
            },
            "results": all_results
        }, f, indent=4)  
    
    

@app.route('/two-variable', methods=["GET", "POST"])
def two_variable():

    all_results = None
    result_id = None
    error = None

    if request.method == "POST":
        try:
            # get inputs from form and convert to int
            A = int(request.form["A"])
            B = int(request.form["B"])
            C = int(request.form["C"])
            D_min = int(request.form["D_min"])
            E_min = int(request.form["E_min"])

            D_max_raw = request.form.get("D_max")
            E_max_raw = request.form.get("E_max")

            if D_max_raw:
                D_max = int(D_max_raw)
            else:
                D_max = D_min

            if E_max_raw:
                E_max = int(E_max_raw)
            else:
                E_max = E_min

            F = int(request.form["F"])
            k = int(request.form["k"])
            L = int(request.form["L"])
            S = int(request.form["S"])

        except (KeyError, ValueError):
            # handle missing or invalid input
            error = "Invalid input: all parameters must be valid integers. Please check that every field contains a number."
            return render_template("two_variable.html", error=error)

        errors = []

        if D_min > D_max:
            errors.append(
                "D_max cannot be smaller than D_min."
            )

        if E_min > E_max:
            errors.append(
                "E_max cannot be smaller than E_min."
            )

        if errors:
            error = " ".join(errors)
            return render_template("two_variable.html", error=error)

        all_results = []

        for D in range(D_min, D_max + 1):
            for E in range(E_min, E_max + 1):
                sum_coeffs = (
                    compute_two_variable_q_series(
                        A, B, C, D, E, F, k, L, S
                    )
                )

                if sum_coeffs == "ERROR":
                    continue

                prod_coeffs = sum_to_product(
                    sum_coeffs,
                    S
                )

                period = test_periodicity(
                    prod_coeffs
                )

                all_results.append({

                    "D": D,
                    "E": E,

                    "sum": sum_coeffs,
                    "prod": prod_coeffs,
                    "period": period
                })

        # generate unique id for result
        result_id = str(uuid.uuid4())

        base = os.path.join(RESULTS_DIR, "two_" + result_id)

        
        save_two_variable_files(base, A, B, C, D_min, D_max, 
                                E_min, E_max, F, k, L, S, all_results)

    return render_template(
        "two_variable.html",
        all_results=all_results,
        result_id=result_id,
        error=error,
        params=request.form
    )
    

@app.route("/download/two-variable/<result_id>/<filetype>")
def download_two_variable(result_id, filetype):

    if filetype not in ("txt", "csv", "json"):
        return "Invalid file type", 400

    try:
        uuid.UUID(result_id)
        # validate uuid format
    except ValueError:
        return "Invalid result ID", 400

    filepath = os.path.join(RESULTS_DIR, f"two_{result_id}.{filetype}")

    if not os.path.exists(filepath):
        # check file exists
        return "Results not found", 404

    # send file to user for download
    return send_file(
        filepath,
        as_attachment=True,
        download_name=f"two_variable_results.{filetype}"
    )
    


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)