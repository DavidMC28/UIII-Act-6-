from django import forms
from .models import Empleado, Cliente, Venta, Producto, Proveedor, DetalleVenta

class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = '__all__'
        widgets = {
            'fecha_contratacion': forms.DateInput(attrs={'type': 'date'}),
        }

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = '__all__'
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ingrese la dirección completa...'}),
            'correo': forms.EmailInput(attrs={'placeholder': 'ejemplo@correo.com'}),
            'telefono': forms.TextInput(attrs={'placeholder': '+52 123 456 7890'}),
        }
        labels = {
            'id_empleado': 'Empleado Asignado',
        }

class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['id_cliente', 'id_empleado', 'total']
        widgets = {
            'total': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),  # ← CORREGIDO: Quitado 'readonly'
        }
        labels = {
            'id_empleado': 'Empleado que realizó la venta',
            'id_cliente': 'Cliente',
        }

class DetalleVentaForm(forms.ModelForm):
    class Meta:
        model = DetalleVenta
        fields = ['producto', 'cantidad', 'precio_unitario']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'min': '1', 'class': 'cantidad-input'}),
            'precio_unitario': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'precio-input'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Establecer el precio unitario automáticamente basado en el producto seleccionado
        if 'producto' in self.data:
            try:
                producto_id = int(self.data.get('producto'))
                producto = Producto.objects.get(id=producto_id)
                self.fields['precio_unitario'].initial = producto.precio
            except (ValueError, TypeError, Producto.DoesNotExist):
                pass

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = '__all__'
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Dirección completa del proveedor...'}),
            'productos': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Lista de productos que provee...'}),
            'email': forms.EmailInput(attrs={'placeholder': 'proveedor@empresa.com'}),
            'telefono': forms.TextInput(attrs={'placeholder': '+52 123 456 7890'}),
        }
        labels = {
            'empresa': 'Nombre de la Empresa',
            'contacto': 'Persona de Contacto',
        }

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = '__all__'
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Descripción del producto...'}),
            'precio': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'existencias': forms.NumberInput(attrs={'min': '0', 'placeholder': '0'}),
            'nombre': forms.TextInput(attrs={'placeholder': 'Nombre del producto'}),
            'categoria': forms.TextInput(attrs={'placeholder': 'Categoría del producto'}),
        }
        labels = {
            'proveedor': 'Proveedor',
            'existencias': 'Existencias en Inventario',
        }