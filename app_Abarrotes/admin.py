from django.contrib import admin
from .models import Empleado, Cliente, Venta, Producto, Proveedor, DetalleVenta

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'apellido', 'puesto', 'salario', 'fecha_contratacion']
    list_filter = ['puesto', 'fecha_contratacion']
    search_fields = ['nombre', 'apellido', 'puesto']
    list_per_page = 20

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'telefono', 'correo', 'fecha_compra', 'id_empleado', 'productos_comprados_display']
    list_filter = ['fecha_compra', 'id_empleado']
    search_fields = ['nombre', 'telefono', 'correo']
    list_per_page = 20
    
    def productos_comprados_display(self, obj):
        """Muestra los productos comprados por el cliente"""
        return obj.productos_comprados_str()
    productos_comprados_display.short_description = 'Productos Comprados'

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ['id', 'fecha', 'total', 'id_cliente', 'id_empleado']
    list_filter = ['fecha', 'id_empleado']
    search_fields = ['id_cliente__nombre', 'id_empleado__nombre']
    list_per_page = 20
    date_hierarchy = 'fecha'

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ['empresa', 'contacto', 'telefono', 'email', 'categoria']
    list_filter = ['categoria']
    search_fields = ['empresa', 'contacto', 'telefono', 'email', 'productos']
    list_per_page = 20

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'precio', 'proveedor', 'existencias']
    list_filter = ['categoria', 'proveedor']
    search_fields = ['nombre', 'categoria', 'descripcion', 'proveedor__empresa']
    list_per_page = 20
    list_editable = ['precio', 'existencias']

@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ['id', 'venta', 'producto', 'cantidad', 'precio_unitario', 'subtotal']
    list_filter = ['venta', 'producto']
    search_fields = ['venta__id', 'producto__nombre']
    list_per_page = 20