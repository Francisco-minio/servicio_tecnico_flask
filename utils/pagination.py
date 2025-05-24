from flask import request, url_for
from sqlalchemy import desc, asc

class Paginator:
    def __init__(self, query, page=1, per_page=10, order_by=None, order_direction='desc'):
        self.query = query
        self.page = page
        self.per_page = per_page
        self.order_by = order_by
        self.order_direction = order_direction

    def get_page(self):
        """Obtiene los resultados paginados."""
        # Aplicar ordenamiento si está especificado
        if self.order_by:
            direction = desc if self.order_direction == 'desc' else asc
            self.query = self.query.order_by(direction(self.order_by))

        # Paginar resultados
        items = self.query.paginate(
            page=self.page,
            per_page=self.per_page,
            error_out=False
        )
        return items

    @staticmethod
    def get_pagination_params():
        """Obtiene los parámetros de paginación de la request."""
        try:
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 10))
            order_by = request.args.get('order_by')
            order_direction = request.args.get('direction', 'desc')
        except (TypeError, ValueError):
            page = 1
            per_page = 10
            order_by = None
            order_direction = 'desc'
        
        return page, per_page, order_by, order_direction

def get_pagination_urls(pagination, endpoint):
    """Genera URLs para la navegación de la paginación."""
    urls = {
        'first': url_for(endpoint, page=1) if pagination.pages > 0 else None,
        'last': url_for(endpoint, page=pagination.pages) if pagination.pages > 0 else None,
        'next': url_for(endpoint, page=pagination.next_num) if pagination.has_next else None,
        'prev': url_for(endpoint, page=pagination.prev_num) if pagination.has_prev else None,
    }
    return urls

def get_page_items(pagination):
    """Genera la lista de números de página para mostrar."""
    total_pages = pagination.pages
    current_page = pagination.page
    
    # Mostrar máximo 5 páginas
    if total_pages <= 5:
        return list(range(1, total_pages + 1))
    
    # Calcular rango de páginas a mostrar
    if current_page <= 3:
        return list(range(1, 6))
    elif current_page >= total_pages - 2:
        return list(range(total_pages - 4, total_pages + 1))
    else:
        return list(range(current_page - 2, current_page + 3)) 