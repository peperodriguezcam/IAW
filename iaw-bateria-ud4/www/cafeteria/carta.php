<?php
// Batería UD4 · bloque 2 · La carta. Apartado 4 de la UD4.
declare(strict_types=1);

$titulo = 'Carta · Cafetería';
$platos = require __DIR__ . '/inc/platos.php';
require __DIR__ . '/inc/cabecera.php';

// ✍️ 2.2 · Una función euros() que reciba un número (float) y devuelva el precio en texto,
// con dos decimales, coma decimal y el símbolo del euro: 3.2 → «3,20 €».
function euros(float $cantidad): string {
    return number_format($cantidad, 2, ',', '.') . ' €';
}
?>

<h2>La carta</h2>
<ul id="carta">
<?php 
// ✍️ 2.1 · Un <li> por plato: «nombre — precio» (el precio, con tu euros()).
foreach ($platos as $p): 
?>
    <li><?= htmlspecialchars($p['nombre']) ?> — <?= euros((float)$p['precio']) ?></li>
<?php endforeach; ?>
</ul>

<?php 
// ✍️ 2.3 · Suma los precios de todos los platos. Pista: array_column + array_sum.
$total = array_sum(array_column($platos, 'precio'));
?>
<p id="total">Total de la carta: <?= euros((float)$total) ?></p>

<h2>Para vegetarianos</h2>
<?php 
// ✍️ 2.4 · Quédate solo con los vegetarianos (array_filter) y pinta otra lista igual
$vegetarianos = array_filter($platos, fn($p) => $p['vegetariano'] ?? false);
?>
<ul id="vegetarianos">
    <?php foreach ($vegetarianos as $p): ?>
        <li><?= htmlspecialchars($p['nombre']) ?> — <?= euros((float)$p['precio']) ?></li>
    <?php endforeach; ?>
</ul>

</body>
</html>
