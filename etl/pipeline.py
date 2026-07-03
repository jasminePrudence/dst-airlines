import subprocess
import sys
import signal

SERVICES = [
    ("OpenSky Producer", "etl/extract/extract_opensky.py"),
    ("AVWX Producer", "etl/extract/extract_avwx.py"),
    ("Mongo Consumer", "etl/load/load_mongodb.py"),
    ("PostgreSQL Consumer", "etl/load/load_postgres.py"),
    ("Weather Consumer", "etl/load/load_weather.py")
]

processes = []


def start_service(name, script):
    print(f"🚀 Démarrage de {name}")
    process = subprocess.Popen([sys.executable, script])
    processes.append(process)


def stop_services():
    print("\n🛑 Arrêt du pipeline...")
    for process in processes:
        process.terminate()


def main():

    print("=" * 60)
    print("DST AIRLINES - ETL PIPELINE")
    print("=" * 60)

    for name, script in SERVICES:
        start_service(name, script)

    try:
        for process in processes:
            process.wait()

    except KeyboardInterrupt:
        stop_services()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()

    
# commande: python -m etl.pipeline