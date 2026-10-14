# Índice de la GuíaSección. 
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
      ## Paso 2.1.1. Creación de carpeta SSL y acceder
   Ejecutamos 
         -> mkdir -p nginx/ssl
         -> cd nginx/ssl

      ## Paso 2.1.2. Generamos la clave privada con prime256v1
   Ejecutamos 
	-> openssl ecparam -name prime256v1 -genkey -out nimbusdocs.key

      ## Paso 2.1.3. Generamos el certificado autosignado y comprobamos
   Ejecutamos
	-> openssl req -new -x509 -key nimbusdocs.key -out nimbusdocs.crt -days 365 -subj "/CN=pubdocs.iaw.local/O=NimbusDocs Lab/C=ES" 
   Comprobamos
	-> ls -l 
	     (Tiene que salir nimbusdocs.crt y nimbusdocs.key)

    ## Paso 2.2. Creación de nginx/Dockerfile
   Ejecutamos
	-> mkdir -p nginx
	-> nano nginx/Dockerfile
		Dentro del Dockerfile escribimos:
			FROM nginx:alpine
			EXPOSE 80 443

    ## Paso 2.3. Configuración del archivo global
      ## Paso 2.3.1 Creación de archivo
   Ejecutamos
	-> nano nginx/nginx.conf
		Dentro del fichero, el siguiente contenido:
			user nginx;
			worker_processes auto;
			error_log /var/log/nginx/error.log warn;
			pid /var/run/nginx.pid;

			events {
			    worker_connections 1024;
			}

			http {
			    include /etc/nginx/mime.types;
			    default_type application/octet-stream;

			    # Definición de la zona de Rate Limiting (3 peticiones/segundo)
			    limit_req_zone $binary_remote_addr zone=limite_nimbus:10m rate=3r/s;

			    include /etc/nginx/conf.d/*.conf;
			}
	
    ## Paso 2.4. Configuración de Proxy INverso, TLS y Seguridad
      ## Paso 2.4.1. Creación de carpeta
   Ejecutamos
	-> mkdir -p nginx/conf.d
	-> nano nginx/conf.d/nimbusdocs.conf
		Dentro del fichero ponemos este contenido:
			# 1. Redirección HTTP (80) a HTTPS (443)
			server {
			    listen 80;
			    server_name pubdocs.iaw.local privdocs.iaw.local;

			    return 301 https://$host$request_uri;
			}

			# 2. Bloque Servidor HTTPS (443)
			server {
			    listen 443 ssl;
			    server_name pubdocs.iaw.local privdocs.iaw.local;

			    # Certificados SSL ECDSA
			    ssl_certificate /etc/nginx/ssl/nimbusdocs.crt;
			    ssl_certificate_key /etc/nginx/ssl/nimbusdocs.key;

			    # Protocolos seguros exigidos (TLS 1.2 y TLS 1.3)
			    ssl_protocols TLSv1.2 TLSv1.3;
			    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305;
			    ssl_prefer_server_ciphers on;

			    # Cabeceras de seguridad
			    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
			    add_header X-Content-Type-Options "nosniff" always;
			    add_header X-Frame-Options "SAMEORIGIN" always;

			    location / {
			        # Aplicar Rate Limiting (Permite ráfagas de 3 peticiones extra sin retardo)
			        limit_req zone=limite_nimbus burst=3 nodelay;

			        # Comunicación Proxy Inverso hacia el contenedor Backend de Apache
			        proxy_pass http://apache_backend:8080;
			        
			        # Inyección de cabeceras HTTP hacia el backend
			        proxy_set_header Host $host;
			        proxy_set_header X-Real-IP $remote_addr;
			        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
			        proxy_set_header X-Forwarded-Proto $scheme;
			    }
			}

    ## Paso 2.5. Actualizar el docker-compose.yml para unir Nginx + Apache
   Editamos el docker-compose.yml en practica1/
	Dentro del fichero, reemplazamos todo lo que haya por esto:
		version: '3.8'

		services:
		  apache_backend:
		    build: ./apache
		    container_name: apache_backend
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
		    networks:
		      - nimbus_net

		  nginx_frontend:
		    build: ./nginx
		    container_name: nginx_frontend
		    ports:
		      - "80:80"
		      - "443:443"
		    volumes:
		      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
		      - ./nginx/conf.d/nimbusdocs.conf:/etc/nginx/conf.d/nimbusdocs.conf:ro
		      - ./nginx/ssl:/etc/nginx/ssl:ro
		    depends_on:
		      - apache_backend
		    networks:
		      - nimbus_net

		networks:
		  nimbus_net:
		    driver: bridge   

    ## Paso 2.6. Despliegue y prueba de validación de la fase 2
   Ejecutamos -> docker compose up -d --build

	Ejecutamos las comprobaciones con curl:
		Probamos redirección HTTP -> HTTPS (debe responder código 301)
	-> curl -i -H "Host: pubdocs.iaw.local" http://localhost/

		Probamos marca pública en HTTPS cifrado (-k para cert. autofirmado)
	-> curl -k -H "Host: pubdocs.iaw.local" https://localhost/

		Probamos marca privada en HTTPS:
	-> curl -k -H "Host: privdocs.iaw.local" https://localhost/

		Probamos la negociación SSL/TLS y el certificado ECDSA
	-> openssl s_client -connect localhost:443 -tls1_3

		Probamos el bloqueo por Rate Limiting (Bucle x 10 peticiones)
	-> for i in {1..10}; do curl -k -o /dev/null -s -w "%{http_code}\n" https://localhost/ -H "Host: pubdocs.iaw.local"; done

    ## Paso 3. Diagnostico de fallos
      ## Paso 3.1. Apagamos el servicio
   Ejecutamos -> docker restart apache_backend

      ## Paso 3.2. Comentamos en apache/sites/pubdocs.conf
   Ejecutamos -> nano /apache/sites/pubdocs.conf y comentamos el ServerName

      ## Paso 3.3. Probamos con curl
   Ejecutamos -> curl -k -H "Host: pubdocs.conf" https://localhost/
   Debe darnos el Catch-All, entonces estará correcto.

FIN de la práctica nº1 de IAW.
~ Pepe Rodriguez
