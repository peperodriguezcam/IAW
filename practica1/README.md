# Índice de la GuíaSección 
Sección 1: Diseño y Requisitos de Originalidad   
Sección 2: Fase 1 — Backend Apache Multi-Marca   
Sección 3: Fase 2 — Terminación TLS en Nginx   
Sección 4: Fase 2 — Seguridad y Límite de Peticiones (Rate Limiting)   
Sección 5: Fase 3 — Diagnóstico Provocado (Tablas y Fallos)   
Sección 6: Guía para la Defensa Oral y Práctica en Vivo   

# Diseño y Requisitos
Dominios elegidos:
  pubdocs.iaw.local - Público
  privdocs.iaw.local - Privado
Función -> Separar los accesos públicos de los recursos internos restringidos (privados)

MPM elegido: mpm_event
  Función -> Es más escalable y a la hora de meter tráfico es muchísimo mejor prefork
  y worker

# Estructura de la práctica
nimbusdocs-docker/
├── docker-compose.yml
├── apache/
│   ├── Dockerfile
│   ├── ports.conf
│   ├── sites/
│   │   ├── 000-default-catchall.conf
│   │   ├── pubdocs.conf
│   │   └── privdocs.conf
│   └── html/
│       ├── default/
│       │   └── index.html
│       ├── pubdocs/
│       │   └── index.html
│       └── privdocs/
│           ├── index.html
│           └── secrets/
│               └── vault_key.env
└── nginx/
    ├── Dockerfile
    ├── nginx.conf
    ├── conf.d/
    │   └── nimbusdocs.conf
    └── ssl/
        ├── nimbusdocs.crt
        └── nimbusdocs.key

   ## Comandos para la creación de la estructura
   mkdir -p practica1/apache/sites
   mkdir -p practica1/apache/html/default
   mkdir -p practica1/apache/html/pubdocs
   mkdir -p practica1/apache/html/privdocs/secrets
   mkdir -p practica1/nginx/conf.d
   mkdir -p practica1/nginx/ssl

# Fase 1 - Backend Apache Multi-Marca
    ## Fase 1.1. Creación de Dockerfile en apache/
   Me quedo en Gemini en el Paso 2. 

