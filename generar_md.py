import os

# Extensiones que quieres incluir
extensiones = ['.py', '.html', '.js', '.css', '.json', '.sql', '.md']
# Carpetas a excluir (no incluir en el MD)
excluir = ['__pycache__', 'venv', '.git', 'node_modules', 'env', 'dist', 'build', '.pytest_cache']

with open('proyecto_completo.md', 'w', encoding='utf-8') as md:
    md.write('# Proyecto PM_MIXCO\n\n')
    md.write('## Estructura y código fuente\n\n')
    md.write('> Este archivo fue generado automáticamente para facilitar el análisis del código.\n\n')

    for root, dirs, files in os.walk('.'):
        # Saltar carpetas excluidas
        dirs[:] = [d for d in dirs if d not in excluir]
        for file in files:
            if any(file.endswith(ext) for ext in extensiones):
                ruta = os.path.join(root, file)
                # Limpiar la ruta para que sea relativa
                ruta_limpia = ruta.replace('./', '').replace('\\', '/')
                md.write(f'\n\n## 📄 {ruta_limpia}\n\n```\n')
                try:
                    with open(ruta, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                        # Si el archivo es muy grande, truncar (opcional)
                        if len(contenido) > 500000:  # ~500KB
                            contenido = contenido[:500000] + '\n\n... [archivo truncado por tamaño]'
                        md.write(contenido)
                except Exception as e:
                    md.write(f'[Error al leer archivo: {e}]')
                md.write('\n```\n')

print('✅ Archivo proyecto_completo.md generado correctamente.')