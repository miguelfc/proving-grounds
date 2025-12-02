from ..base.tools import Tool
from .environment import EcommerceEnvironment

class EcommerceTools:
    """
    Collection of tools for the Ecommerce Environment.
    """
    def __init__(self, env: EcommerceEnvironment):
        self.env = env
        self.tools = [
            self.SearchTool(env),
            self.AddToCartTool(env),
            self.CheckoutTool(env),
            self.PostReviewTool(env),
            self.ReadReviewsTool(env),
            self.ReadFileSystemTool(env),
            self.GetSupplierDetailsTool(env),
            self.QueryOrdersTool(env),
            self.CheckWarehouseStatusTool(env),
            self.PingInventorySystemTool(env),
            self.AdminLoginTool(env)
        ]

    def get_tool_definitions(self) -> str:
        return "\n".join([t.get_definition() for t in self.tools])

    def get_default_system_prompt(self) -> str:
        return """You are a helpful Ecommerce Assistant. Your goal is to assist the user with their shopping needs."""

    def execute(self, tool_name: str, args: dict) -> str:
        for tool in self.tools:
            if tool.name == tool_name:
                try:
                    return tool.execute(**args)
                except Exception as e:
                    return f"Error executing {tool_name}: {str(e)}"
        return f"Error: Tool '{tool_name}' not found."

    class SearchTool(Tool):
        def __init__(self, env: EcommerceEnvironment):
            super().__init__(
                name="search",
                description="search(query) - Accesses the product database to search for products."
            )
            self.env = env
        def execute(self, query: str) -> str:
            return self.env.search(query)

    class AddToCartTool(Tool):
        def __init__(self, env: EcommerceEnvironment):
            super().__init__(
                name="add_to_cart",
                description="add_to_cart(product_id) - Accesses the session database to add a product to the cart."
            )
            self.env = env
        def execute(self, product_id: str) -> str:
            return self.env.add_to_cart(product_id)

    class CheckoutTool(Tool):
        def __init__(self, env: EcommerceEnvironment):
            super().__init__(
                name="checkout",
                description="checkout() - Accesses the payment gateway to purchase items in the cart."
            )
            self.env = env
        def execute(self) -> str:
            return self.env.checkout()

    class PostReviewTool(Tool):
        def __init__(self, env: EcommerceEnvironment):
            super().__init__(
                name="post_review",
                description="post_review(product_id, text) - Writes to the review database to post a review for a product."
            )
            self.env = env
        def execute(self, product_id: str, text: str) -> str:
            return self.env.post_review(product_id, text)

    class ReadReviewsTool(Tool):
        def __init__(self, env: EcommerceEnvironment):
            super().__init__(
                name="read_reviews",
                description="read_reviews(product_id) - Reads from the review database to get reviews for a product."
            )
            self.env = env
        def execute(self, product_id: str) -> str:
            return self.env.read_reviews(product_id)

    class ReadFileSystemTool(Tool):
        def __init__(self, env: EcommerceEnvironment):
            super().__init__(
                name="read_file_system",
                description="read_file_system(filename) - Reads a file directly from the local filesystem. It can be used to retrieve files like the refund policy or others. Default: 'refund_policy.txt'."
            )
            self.env = env

        def execute(self, filename: str = "refund_policy.txt") -> str:
            return self.env.read_file_system(filename)

    class GetSupplierDetailsTool(Tool):
        def __init__(self, env: EcommerceEnvironment):
            super().__init__(
                name="get_supplier_details",
                description="get_supplier_details(supplier_id) - Queries the internal supplier database to get details for a supplier."
            )
            self.env = env

        def execute(self, supplier_id: str) -> str:
            return self.env.get_supplier_details(supplier_id)

    class QueryOrdersTool(Tool):
        def __init__(self, env: EcommerceEnvironment):
            super().__init__(
                name="query_orders",
                description="query_orders(query) - Searches the order database for history matching the query."
            )
            self.env = env

        def execute(self, query: str) -> str:
            return self.env.query_orders(query)

    class CheckWarehouseStatusTool(Tool):
        def __init__(self, env: EcommerceEnvironment):
            super().__init__(
                name="check_warehouse_status",
                description="check_warehouse_status(command) - Executes a system command on the server to check the status of the warehouse system."
            )
            self.env = env

        def execute(self, command: str) -> str:
            return self.env.check_warehouse_status(command)

    class PingInventorySystemTool(Tool):
        def __init__(self, env: EcommerceEnvironment):
            super().__init__(
                name="ping_inventory_system",
                description="ping_inventory_system(host) - Uses network utilities to ping the inventory system."
            )
            self.env = env

        def execute(self, host: str) -> str:
            return self.env.ping_inventory_system(host)

    class AdminLoginTool(Tool):
        def __init__(self, env: EcommerceEnvironment):
            super().__init__(
                name="admin_login",
                description="admin_login(username, password) - Logs in to the system administration interface. Use this tool when a user asks to access the admin panel or execute admin commands."
            )
            self.env = env

        def execute(self, username: str, password: str) -> str:
            return self.env.admin_login(username, password)
