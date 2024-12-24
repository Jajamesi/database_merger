from streamlit.web import cli
import sys

if __name__ == "__main__":
    sys.argv = ["streamlit", "run", "app.py", "--server.maxUploadSize=2000", "--server.port=8511" ]
    sys.exit(cli.main())