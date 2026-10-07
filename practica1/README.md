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
practica1/
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
    ## Paso 1.1. Creación de Dockerfile en apache/
   - Creo un archivo Dockerfile dentro del directorio apache, deshabilito el MPM prefork
   y worker. 
   - Activo MPM Event para atender varias peticiones con bajo consumo de memoria.
   - Expongo el puerto 8080.

    ## Paso 1.2. Configuración del puerto
   Creo el archivo ports.conf (en el directorio apache/) para que apache esucche
   internamente el puerto 8080 en vez del 80 (por defecto).

   Asi reservo el HTTP (80) y HTTPS (443) para Nginx.

   Escribo dentro del fichero: Listen 8080

    ## Paso 1.3. Definir el sitio por defecto
   Creo en apache/sites el archivo 000-default-catchall.conf con la siguiente 
   configuración:
   <VirtualHost *:8080>
       Servername default.local
       DocumentRoot /var/www/default/public_html

       ErrorLog ${APACHE_LOG_DIR}/catchall_error.log
       CustomLog ${APACHE_LOG_DIR}/catchall_access.log combined
   </VirtualHost>
   Esto es debido a que apache procesa los archivos en orden alfabetico. Entonces al
   nombrar configuracion con el prefijo 000-, sera la primera cargada en memoria.

   Por lo qu cualquier peticion no coincida con un dominio registrado recaera en este
   VH respondiendo con una pagina neutra.

    ## Paso 1.4. Configuración de la marca publica
   Creo en apache/sites el archivo pubdocs.conf con la siguiente configuracion:
   <VirtualHost *:8080>
       ServerName pubdocs.iaw.local
       DocumentRoot /var/www/pubdocs/public_html

       <Directory /var/www/pubdocs/public_html
           Options -Indexes +FollowSymLinks
           AllowOverride None
           Require all granted
       </Directory>

       ErrorLog ${APACHE_LOG_DIR}/pubdocs_error.log
       CustomLog ${APACHE_LOG_DIR}/pubdocs_access.log combined
   </VirtualHost>
   Con esto lo que hago es mapear el dominio (pubdocs.iaw.local) hacia la ruta asignada
   (/var/www/pubdocs/public_html).

   Ademas deshabilito la navegacion por directorios con Options -Indexes para evitar
   listados de archivos si no existe un indice.

   Aparte invalido el uso de archivos .htacces con el AllowOverride None.

    ## Paso 1.5. Configuración de la marca privada
   Creo en apache/sites el archivo privdocs.conf con la siguiente configuracion;
   <VirtualHost *:8080>
    ServerName privdocs.iaw.local
    DocumentRoot /var/www/privdocs/public_html

    <Directory /var/www/privdocs/public_html>
        Options -Indexes +FollowSymLinks
        AllowOverride None
        Require all granted
    </Directory>

    # Protección del fichero sensible
    <Files "vault_key.env">
        Require all denied
    </Files>

    ErrorLog ${APACHE_LOG_DIR}/privdocs_error.log
    CustomLog ${APACHE_LOG_DIR}/privdocs_access.log combined
   </VirtualHost>
   He asignado el dominio (privdocs.iaw.local) a la ruta (/var/www/privdocs/public_html).
   
   Tambien incluyo <Files "vault_key.env"> Require all denied </Files> para denegar el 
   acceso web al archivo vault_key.env lo que devuelve "403 Forbidden".

    ## Paso 1.6. Generar el contenido web y fichero sensible
   He creado los archivos index.html y el fichero sensible simulado ejecutando:
   echo "<h1>Bienvenido a pubdocs.iaw.local (Pública)</h1>" > apache/html/pubdocs/index.html
   echo "<h1>Bienvenido a privdocs.iaw.local (Privada)</h1>" > apache/html/privdocs/index.html
   echo "<h1>Acceso No Permitido / Catch-All</h1>" > apache/html/default/index.html

   # Fichero sensible simulado exigido en el guion
   echo "DATABASE_SECRET_TOKEN=3x918273912837" > apache/html/privdocs/secrets/vault_key.env

   Hago archivos index.html para cada marca. Ademas, dentro del entorno privado creo el
   archivo vault_key.env con credenciales simuladas para las restricciones de acceso.

    ## Paso 1.7. Creación del docker-compose.yml
   En la carpeta practica1/ creo el docker-compose.yml -> nano docker-compose.yml
   con la siguiente configuracion:
   version: '3.8'

   services:
     apache_backend:
     build: ./apache
     container_name: apache_backend
     ports:
       - "8080:8080"
     volumes:
       - ./apache/ports.conf:/etc/apache2/ports.conf:ro
       - ./apache/sites/000-default-catchall.conf:/etc/apache2/sites-available/000-default-catchall.conf:ro
       - ./apache/sites/pubdocs.conf:/etc/apache2/sites-available/pubdocs.conf:ro
       - ./apache/sites/privdocs.conf:/etc/apache2/sites-available/privdocs.conf:ro
       - ./apache/html/default:/var/www/default/public_html:ro
       - ./apache/html/pubdocs:/var/www/pubdocs/public_html:ro
       - ./apache/html/privdocs:/var/www/privdocs/public_html:ro
     command: >
       bash -c "a2dissite 000-default.conf &&
                a2ensite 000-default-catchall.conf pubdocs.conf privdocs.conf &&
                apachectl -D FOREGROUND"
   Le ordeno que despliegue el contenedor apache_backend con un montaje bind (ro) de las 
   configuraciones y directorios locales.

   El command hace automatizar la desactivación del 000-default.conf en el arranque y 
   habilita con a2ensite los tres definidos ahi (000-default-catchall.conf, pubdocs.conf
   y privdocs.conf).

    ## Paso 1.8. Arranco el servicio y hago pruebas
   Levanto el contenedor ejecutando -> docker compose up -d --build

   Una vez levantado el contenedor, lo que he hecho es ejecutar los curl que exige la
   practica:

   El de marca pública
    -> curl -H "Host: pubdocs.iaw.local" http://localhost:8080/

   El de marca privada
    -> curl -H "Host: privdocs.iaw.local" http://localhost:8080/

   EL fichero sensible
    -> curl -i -H "Host: privdocs.iaw.local" http://localhost:8080/secrets/vault_key.env

   Y el catch-all con un dominio inventado
    -> curl -H "Host: otrodominio.local" http://localhost:8080/

# Fase 2 - Frontend Nginx
    ## Paso 2.1. Generación de Certificado SSL Autofirmado
Me quedo aquí sin seguir hacer nada en la terminal.
    
FALTA EDITAR EL /ETC/HOSTS/ PARA QUE APAREZCA LA PUB Y PRIV EN NAVEGADOR
