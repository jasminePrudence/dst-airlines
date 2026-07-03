import subprocess
import sys
import signal
from pathlib import Path
import time

#objets Path pour fonctionner de manière fiable sous Windows, Linux et dans Docker
BASE_DIR = Path(__file__).resolve().parent.parent

SERVICES = [
    ("OpenSky Producer", "etl.extract.extract_opensky"),
    ("AviationStack Producer", "etl.extract.extract_aviationstack"),
    ("AVWX Producer", "etl.extract.extract_avwx"),
    ("Mongo Consumer", "etl.load.load_mongodb"),
    ("PostgreSQL Consumer", "etl.load.load_postgres"),
    ("Weather Consumer", "etl.load.load_weather"),
]

processes = []

def start_service(name, module):
    print(f"🚀 Démarrage de {name}")
    process = subprocess.Popen(
        [sys.executable, "-m", module]
    )
    processes.append(process)
    print(f"   PID : {process.pid}")
  
def stop_services():
    print("\n🛑 Arrêt du pipeline...")
    for process in processes:
        process.terminate()
    for process in processes:
        process.wait()

    print("✅ Tous les services sont arrêtés.")
    
def main():

    print("=" * 60)
    print("DST AIRLINES - ETL PIPELINE")
    print("=" * 60)

    for name, script in SERVICES:
        start_service(name, script)
        time.sleep(2)

    print("\n✅ Tous les services sont démarrés.\n")
    print("Appuyez sur CTRL+C pour arrêter le pipeline.\n")

    try:
        for process in processes:
            process.wait()
    except KeyboardInterrupt:
        stop_services()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
   
# commande ULTIME: docker exec -it dst_python bash
# puis cd /app
# enfin python -m etl.pipeline