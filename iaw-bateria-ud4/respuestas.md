# Explícalo con tus palabras

Cuando tengas el comprobador en verde, contesta aquí sin mirar los apuntes (2–4 líneas cada una).
Es lo que te preguntarán en la defensa de la práctica.

1. ¿Qué pasa si a Nginx le falta el bloque `location ~ \.php$`? ¿Por qué es peligroso?
Porque nginx serviría el código fuente en texto plano, exponiendo contraseñas y claves secretas.
2. ¿Para qué sirve `try_files $uri =404;` dentro del bloque de PHP? ¿Qué hace Nginx con un `.php` que no existe, con él y sin él?
Comprueba que el archivo exista. Con él da 404; sin él, PHP-FPM procesa ficheros inexistentes, facilitando ataques de ejecución de código.
3. En `pedido.php`, ¿por qué el XSS se arregla al **imprimir** (con `e()`) y no al leer el formulario?
El problema no es leer el dato, sino pintarlo en el navegador sin escapar (e()), donde se interpreta como script malicioso.
4. ¿Por qué en producción `display_errors` va a `Off`, pero `log_errors` a `On`? ¿Qué aprendería un atacante de un error en pantalla?
Oculta información sensible (rutas, versiones, estructura de BD) al atacante y registra los fallos de forma segura en logs.
5. Explica de dónde sale tu `pm.max_children`. ¿Qué pasa si te quedas corto? ¿Y si te pasas?
Se calcula con la RAM disponible y el consumo por proceso. Si te quedas corto, hay timeout (504); si te pasas, colapsa la memoria RAM.
