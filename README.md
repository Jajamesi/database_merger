- Клонируешь
```
git clone https://github.com/Jajamesi/database_merger.git
```

- Закачиваешь пакеты. Питон 3.11+
```
pip install -r requirements.txt
```

- В корень проекта распаковываешь игрушечный диск М, чтобы был вид
database_merger/
>└── M/  
>    └── Количественные исследования/  
>        ├── рег1  
>        └── рег2  
>└── все остальные скрипты  

- Запускаешься из launcher.py - если будет ругаться, поменяй порт тут `"--server.port=8511"`
