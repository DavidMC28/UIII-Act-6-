from django.db import models
from django.db.models import Sum, F

class Empleado(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    puesto = models.CharField(max_length=100)
    salario = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_contratacion = models.DateField()
    foto = models.ImageField(upload_to='empleados/', null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Proveedor(models.Model):
    empresa = models.CharField(max_length=200)
    contacto = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15)
    email = models.EmailField()
    direccion = models.TextField()
    categoria = models.CharField(max_length=100)
    productos = models.TextField(help_text="Productos que provee")
    foto = models.ImageField(upload_to='proveedores/', null=True, blank=True)

    def __str__(self):
        return f"{self.empresa} - {self.contacto}"

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='productos_suministrados')
    descripcion = models.TextField(blank=True)
    existencias = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.nombre} - ${self.precio}"

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15)
    correo = models.EmailField()
    fecha_compra = models.DateField(auto_now_add=True)
    direccion = models.TextField()
    id_empleado = models.ForeignKey('Empleado', on_delete=models.CASCADE, related_name='clientes_atendidos')
    
    def __str__(self):
        return f"{self.nombre} - {self.telefono}"
    
    def productos_comprados(self):
        """Obtiene los productos que ha comprado este cliente"""
        ventas = self.compras_realizadas.all()
        productos_comprados = []
        for venta in ventas:
            for detalle in venta.detalles.all():
                productos_comprados.append(detalle.producto)
        return productos_comprados
    
    def ultimo_producto_comprado(self):
        """Obtiene el último producto comprado por el cliente"""
        ultima_venta = self.compras_realizadas.order_by('-fecha').first()
        if ultima_venta and ultima_venta.detalles.exists():
            return ultima_venta.detalles.first().producto
        return None
    
    def productos_comprados_str(self):
        """Retorna string con los productos comprados para mostrar en admin"""
        productos = self.productos_comprados()
        if productos:
            return ", ".join([p.nombre for p in productos[:3]]) + (f" y {len(productos)-3} más..." if len(productos) > 3 else "")
        return "Sin compras"

class Venta(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    id_empleado = models.ForeignKey('Empleado', on_delete=models.CASCADE, related_name='ventas_realizadas')
    id_cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE, related_name='compras_realizadas')
    
    def __str__(self):
        return f"Venta {self.id} - {self.fecha.strftime('%d/%m/%Y')} - ${self.total}"
    
    def save(self, *args, **kwargs):
        # Calcular el total automáticamente antes de guardar
        if self.pk:  # Si la venta ya existe
            total_detalles = self.detalles.aggregate(
                total=Sum(F('cantidad') * F('precio_unitario'))
            )['total'] or 0
            self.total = total_detalles
        super().save(*args, **kwargs)

class DetalleVenta(models.Model):
    venta = models.ForeignKey('Venta', on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE, related_name='detalles_venta')
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        # Actualizar el total de la venta
        self.venta.save()
    
    def __str__(self):
        return f"Detalle {self.id} - {self.producto.nombre} x{self.cantidad}"