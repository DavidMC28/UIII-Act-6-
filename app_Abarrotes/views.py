from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages
from .models import Empleado, Cliente, Venta, Producto, Proveedor, DetalleVenta
from .forms import EmpleadoForm, ClienteForm, VentaForm, ProductoForm, ProveedorForm, DetalleVentaForm

def inicio(request):
    return render(request, 'inicio.html')

# ========== VISTAS PARA EMPLEADOS ==========
def ver_empleados(request):
    empleados = Empleado.objects.all()
    return render(request, 'empleado/ver_empleados.html', {'empleados': empleados})

def agregar_empleado(request):
    if request.method == 'POST':
        form = EmpleadoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empleado agregado correctamente.')
            return redirect('ver_empleados')
    else:
        form = EmpleadoForm()
    return render(request, 'empleado/agregar_empleado.html', {'form': form})

def actualizar_empleado(request, pk):
    empleado = get_object_or_404(Empleado, pk=pk)
    if request.method == 'POST':
        form = EmpleadoForm(request.POST, request.FILES, instance=empleado)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empleado actualizado correctamente.')
            return redirect('ver_empleados')
    else:
        form = EmpleadoForm(instance=empleado)
    return render(request, 'empleado/actualizar_empleado.html', {'form': form})

def borrar_empleado(request, pk):
    empleado = get_object_or_404(Empleado, pk=pk)
    if request.method == 'POST':
        empleado.delete()
        messages.success(request, 'Empleado eliminado correctamente.')
        return redirect('ver_empleados')
    return render(request, 'empleado/borrar_empleado.html', {'empleado': empleado})

# ========== VISTAS PARA CLIENTES ==========
def ver_clientes(request):
    clientes = Cliente.objects.all().select_related('id_empleado').prefetch_related(
        'compras_realizadas__detalles__producto'
    )
    
    # Agregar información de productos comprados a cada cliente
    for cliente in clientes:
        cliente.productos_comprados_info = cliente.productos_comprados_str()
        cliente.total_compras = cliente.compras_realizadas.count()
    
    return render(request, 'cliente/ver_clientes.html', {'clientes': clientes})

def agregar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente agregado correctamente.')
            return redirect('ver_clientes')
    else:
        form = ClienteForm()
    return render(request, 'cliente/agregar_cliente.html', {'form': form})

def actualizar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente actualizado correctamente.')
            return redirect('ver_clientes')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'cliente/actualizar_cliente.html', {'form': form})

def borrar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        messages.success(request, 'Cliente eliminado correctamente.')
        return redirect('ver_clientes')
    return render(request, 'cliente/borrar_cliente.html', {'cliente': cliente})

def detalle_cliente(request, pk):
    """Vista para ver el detalle completo de un cliente y sus productos comprados"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # Obtener todas las ventas del cliente con sus detalles
    ventas = cliente.compras_realizadas.all().prefetch_related('detalles__producto')
    
    # Obtener todos los productos comprados
    productos_comprados = []
    for venta in ventas:
        for detalle in venta.detalles.all():
            productos_comprados.append({
                'producto': detalle.producto,
                'cantidad': detalle.cantidad,
                'precio_unitario': detalle.precio_unitario,
                'subtotal': detalle.subtotal,
                'fecha_venta': venta.fecha
            })
    
    context = {
        'cliente': cliente,
        'ventas': ventas,
        'productos_comprados': productos_comprados,
        'total_ventas': ventas.count(),
        'total_gastado': sum(venta.total for venta in ventas)
    }
    
    return render(request, 'cliente/detalle_cliente.html', context)

# ========== VISTAS PARA VENTAS ==========
def ver_ventas(request):
    ventas = Venta.objects.all().select_related('id_cliente', 'id_empleado').prefetch_related('detalles__producto')
    return render(request, 'venta/ver_ventas.html', {'ventas': ventas})

def agregar_venta(request):
    if request.method == 'POST':
        venta_form = VentaForm(request.POST)
        if venta_form.is_valid():
            try:
                with transaction.atomic():
                    venta = venta_form.save(commit=False)
                    venta.save()
                    
                    # Obtener todos los productos del formulario
                    productos_ids = request.POST.getlist('producto')
                    cantidades = request.POST.getlist('cantidad')
                    precios = request.POST.getlist('precio')
                    
                    total_venta = 0
                    detalles_creados = 0
                    
                    # Validar que haya al menos un producto
                    if not any(productos_ids):
                        messages.error(request, 'Debe agregar al menos un producto a la venta.')
                        return render(request, 'venta/agregar_venta.html', {
                            'venta_form': venta_form,
                            'productos': Producto.objects.all(),
                        })
                    
                    # Procesar todos los productos
                    for i in range(len(productos_ids)):
                        if productos_ids[i] and cantidades[i] and precios[i]:
                            try:
                                producto = Producto.objects.get(id=productos_ids[i])
                                cantidad = int(cantidades[i])
                                precio_unitario = float(precios[i])
                                
                                # Validar stock disponible
                                if cantidad > producto.existencias:
                                    messages.error(request, f'Stock insuficiente para {producto.nombre}. Stock disponible: {producto.existencias}')
                                    return redirect('agregar_venta')
                                
                                subtotal = cantidad * precio_unitario
                                total_venta += subtotal
                                
                                # Crear detalle de venta
                                DetalleVenta.objects.create(
                                    venta=venta,
                                    producto=producto,
                                    cantidad=cantidad,
                                    precio_unitario=precio_unitario,
                                    subtotal=subtotal
                                )
                                
                                # Actualizar stock del producto
                                producto.existencias -= cantidad
                                producto.save()
                                
                                detalles_creados += 1
                                
                            except (Producto.DoesNotExist, ValueError) as e:
                                messages.error(request, f'Error con el producto en posición {i+1}: {str(e)}')
                                return redirect('agregar_venta')
                    
                    # Verificar que se hayan creado detalles
                    if detalles_creados == 0:
                        messages.error(request, 'Debe agregar al menos un producto válido a la venta.')
                        venta.delete()  # Eliminar la venta vacía
                        return redirect('agregar_venta')
                    
                    venta.total = total_venta
                    venta.save()
                    messages.success(request, f'Venta registrada correctamente con {detalles_creados} producto(s).')
                    return redirect('ver_ventas')
                    
            except Exception as e:
                messages.error(request, f'Error al agregar la venta: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        venta_form = VentaForm()
    
    productos = Producto.objects.filter(existencias__gt=0)  # Solo productos con stock
    detalle_form = DetalleVentaForm()
    
    return render(request, 'venta/agregar_venta.html', {
        'venta_form': venta_form,
        'detalle_form': detalle_form,
        'productos': productos,
    })

def actualizar_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    detalles = venta.detalles.all()
    
    if request.method == 'POST':
        venta_form = VentaForm(request.POST, instance=venta)
        
        if venta_form.is_valid():
            try:
                with transaction.atomic():
                    # Guardar datos básicos de la venta
                    venta = venta_form.save()
                    
                    # Restaurar stock de productos anteriores
                    for detalle in detalles:
                        producto = detalle.producto
                        producto.existencias += detalle.cantidad
                        producto.save()
                    
                    # Eliminar detalles existentes
                    venta.detalles.all().delete()
                    
                    # Procesar nuevos detalles
                    productos_ids = request.POST.getlist('producto')
                    cantidades = request.POST.getlist('cantidad')
                    precios = request.POST.getlist('precio')
                    
                    total_venta = 0
                    detalles_creados = 0
                    
                    for i in range(len(productos_ids)):
                        if productos_ids[i] and cantidades[i] and precios[i]:
                            producto = Producto.objects.get(id=productos_ids[i])
                            cantidad = int(cantidades[i])
                            precio_unitario = float(precios[i])
                            
                            # Validar stock disponible
                            if cantidad > producto.existencias:
                                messages.error(request, f'Stock insuficiente para {producto.nombre}. Stock disponible: {producto.existencias}')
                                return redirect('actualizar_venta', pk=pk)
                            
                            subtotal = cantidad * precio_unitario
                            total_venta += subtotal
                            
                            DetalleVenta.objects.create(
                                venta=venta,
                                producto=producto,
                                cantidad=cantidad,
                                precio_unitario=precio_unitario,
                                subtotal=subtotal
                            )
                            
                            # Actualizar stock del producto
                            producto.existencias -= cantidad
                            producto.save()
                            
                            detalles_creados += 1
                    
                    # Actualizar total de la venta
                    venta.total = total_venta
                    venta.save()
                    
                    messages.success(request, f'Venta actualizada correctamente con {detalles_creados} producto(s).')
                    return redirect('ver_ventas')
                    
            except Exception as e:
                messages.error(request, f'Error al actualizar la venta: {str(e)}')
                productos = Producto.objects.all()
                return render(request, 'venta/actualizar_venta.html', {
                    'venta_form': venta_form,
                    'detalles': detalles,
                    'productos': productos,
                    'venta': venta,
                })
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    
    else:
        venta_form = VentaForm(instance=venta)
    
    productos = Producto.objects.all()
    return render(request, 'venta/actualizar_venta.html', {
        'venta_form': venta_form,
        'detalles': detalles,
        'productos': productos,
        'venta': venta,
    })

def borrar_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Restaurar stock de productos
                for detalle in venta.detalles.all():
                    producto = detalle.producto
                    producto.existencias += detalle.cantidad
                    producto.save()
                
                venta.delete()
                messages.success(request, 'Venta eliminada correctamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar la venta: {str(e)}')
        return redirect('ver_ventas')
    return render(request, 'venta/borrar_venta.html', {'venta': venta})

def detalle_venta(request, pk):
    venta = get_object_or_404(Venta, pk=pk)
    detalles = venta.detalles.all().select_related('producto')
    return render(request, 'venta/detalle_venta.html', {
        'venta': venta,
        'detalles': detalles
    })

# ========== VISTAS PARA PROVEEDORES ==========
def ver_proveedores(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'proveedor/ver_proveedores.html', {'proveedores': proveedores})

def agregar_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor agregado correctamente.')
            return redirect('ver_proveedores')
    else:
        form = ProveedorForm()
    return render(request, 'proveedor/agregar_proveedor.html', {'form': form})

def actualizar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        form = ProveedorForm(request.POST, request.FILES, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Proveedor actualizado correctamente.')
            return redirect('ver_proveedores')
    else:
        form = ProveedorForm(instance=proveedor)
    return render(request, 'proveedor/actualizar_proveedor.html', {'form': form})

def borrar_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    if request.method == 'POST':
        proveedor.delete()
        messages.success(request, 'Proveedor eliminado correctamente.')
        return redirect('ver_proveedores')
    return render(request, 'proveedor/borrar_proveedor.html', {'proveedor': proveedor})

# ========== VISTAS PARA PRODUCTOS ==========
def ver_productos(request):
    productos = Producto.objects.all().select_related('proveedor')
    return render(request, 'producto/ver_productos.html', {'productos': productos})

def agregar_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto agregado correctamente.')
            return redirect('ver_productos')
    else:
        form = ProductoForm()
    return render(request, 'producto/agregar_producto.html', {'form': form})

def actualizar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado correctamente.')
            return redirect('ver_productos')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'producto/actualizar_producto.html', {'form': form})

def borrar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado correctamente.')
        return redirect('ver_productos')
    return render(request, 'producto/borrar_producto.html', {'producto': producto})