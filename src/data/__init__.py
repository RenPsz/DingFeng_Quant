"__init__.py 的作用就是把 Data/ 变成一个包，同时控制对外暴露哪些接口"
from .data import get_index_data, get_stock_data, refresh_indices