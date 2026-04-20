from flask import Flask, render_template, request, send_file

from product_coefficients_with_periodicity import (
    compute_two_variable_q_series,
    sum_to_product,
    test_periodicity
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


@app.route('/', methods=["GET", "POST"])
def index():

    sum_coeffs = None
    prod_coeffs = None
    period = None
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
            F = int(request.form["F"])
            k = int(request.form["k"])
            L = int(request.form["L"])
            S = int(request.form["S"])

        except (KeyError, ValueError):
            # handle missing or invalid input
            error = "All parameters must be valid integers."
            return render_template("index.html", error=error)

        sum_coeffs = compute_two_variable_q_series(A, B, C, D, E, F, k, L, S)
        prod_coeffs = sum_to_product(sum_coeffs, S)
        period = test_periodicity(prod_coeffs)

        # generate unique id for result
        result_id = str(uuid.uuid4())

        base = os.path.join(RESULTS_DIR, result_id)

        # txt
        with open(f"{base}.txt", "w") as f:
            f.write("Parameters\n")
            f.write(f"A={A}, B={B}, C={C}, D={D}, E={E}, F={F}, k={k}, L={L}, S={S}\n\n")

            f.write("Sum Coefficients\n")
            f.write(str(sum_coeffs) + "\n\n")

            f.write("Product Coefficients\n")
            f.write(str(prod_coeffs) + "\n\n")

            f.write("Periodicity\n")
            f.write(f"Period = {period}\n" if period else "No periodicity detected\n")

        #csv
        with open(f"{base}.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerow(["sep=;"])

            writer.writerow(["Parameter", "Value"])
            for name, val in zip("ABCDEF", [A, B, C, D, E, F]):
                writer.writerow([name, val])

            writer.writerow(["k", k])
            writer.writerow(["L", L])
            writer.writerow(["S", S])

            writer.writerow([])
            writer.writerow(["Index", "Sum_Coeff", "Product_Coeff"])

            for i, (sc, pc) in enumerate(zip(sum_coeffs, prod_coeffs)):
                writer.writerow([i, sc, pc])

            writer.writerow([])
            writer.writerow(["Periodicity", period if period else "None"])
        

        # json
        with open(f"{base}.json", "w") as f:
            json.dump({
                "parameters": {
                    "A": A, "B": B, "C": C, "D": D,
                    "E": E, "F": F, "k": k, "L": L, "S": S
                },
                "sum_coeffs": sum_coeffs,
                "prod_coeffs": prod_coeffs,
                "period": period
            }, f, indent=4)

    return render_template(
        "index.html",
        sum_coeffs=sum_coeffs,
        prod_coeffs=prod_coeffs,
        period=period,
        result_id=result_id,
        error=error
    )


@app.route("/download/<result_id>/<filetype>")
def download(result_id, filetype):

    if filetype not in ("txt", "csv", "json"):
        return "Invalid file type", 400

    try:
        uuid.UUID(result_id)
        # validate uuid format
    except ValueError:
        return "Invalid result ID", 400

    filepath = os.path.join(RESULTS_DIR, f"{result_id}.{filetype}")

    if not os.path.exists(filepath):
        # check file exists
        return "Results not found", 404

    # send file to user for download
    return send_file(
        filepath,
        as_attachment=True,
        download_name=f"results.{filetype}"
    )
    


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)