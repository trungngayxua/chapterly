import tkinter as tk
from tkinter import messagebox, filedialog
import json
import math
from collections import deque


class GraphEditor:
    """
     Lớp chính để tạo và quản lý ứng dụng đồ thị tương tác sử dụng Tkinter.

     Ứng dụng cho phép người dùng:
     - Thêm, xóa, kéo thả đỉnh trên canvas.
     - Thêm, xóa cạnh giữa các đỉnh.
     - Kiểm tra tính liên thông của đồ thị.
     - Tìm đường đi ngắn nhất giữa hai đỉnh.
     - Lưu và tải đồ thị từ file JSON.
    """

    def __init__(self, root):
        """
        Khởi tạo ứng dụng đồ thị với cửa sổ chính Tkinter.

        Tham số:
            root (tk.Tk): Cửa sổ gốc của ứng dụng.
        """
        self.root = root
        self.root.title("Chapterly")

        # Cấu hình giao diện
        self.canvas = tk.Canvas(root, width=800, height=600, bg='white', cursor="hand2")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Frame điều khiển
        self.control_frame = tk.Frame(root, width=200, height=600, bg='lightgray')
        self.control_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Biến trạng thái
        self.nodes = {}
        self.edges = []
        self.node_radius = 20
        self.dragging = False
        self.drag_node = None
        self.current_mode = "select"  # Modes: select, add_node, add_edge, delete

        # Khởi tạo giao diện
        self.setup_ui()

        # Bind sự kiện
        self.canvas.bind("<Button-1>", self.handle_click)
        self.canvas.bind("<B1-Motion>", self.handle_drag)
        self.canvas.bind("<ButtonRelease-1>", self.handle_release)

    def setup_ui(self):
        """
        Thiết lập giao diện người dùng với các nút điều khiển và nhãn trạng thái.

        Các nút bao gồm:
        - Chế độ chọn, thêm đỉnh, thêm cạnh, xóa
        - Kiểm tra liên thông
        - Tìm đường ngắn nhất
        - Lưu, tải và xóa đồ thị
        """
        buttons = [
            ("Chế độ chọn", self.set_select_mode),
            ("Thêm đỉnh", self.set_add_node_mode),
            ("Thêm cạnh", self.set_add_edge_mode),
            ("Xóa", self.set_delete_mode),
            ("Kiểm tra liên thông", self.check_connectivity),
            ("Tìm đường ngắn nhất", self.find_shortest_path),
            ("Lưu đồ thị", self.save_graph),
            ("Tải đồ thị", self.load_graph),
            ("Xóa tất cả", self.clear_all)
        ]

        for text, command in buttons:
            btn = tk.Button(self.control_frame, text=text, command=command)
            btn.pack(fill=tk.X, padx=5, pady=2)

        self.mode_label = tk.Label(self.control_frame, text="Chế độ: Chọn", bg='lightgray')
        self.mode_label.pack(fill=tk.X, padx=5, pady=10)

    # ========== CÁC CHẾ ĐỘ ==========
    def set_select_mode(self):
        """Chuyển sang chế độ chọn đỉnh để có thể kéo thả."""
        self.current_mode = "select"
        self.mode_label.config(text="Chế độ: Chọn")
        self.canvas.config(cursor="hand2")

    def set_add_node_mode(self):
        """Chuyển sang chế độ thêm đỉnh mới."""
        self.current_mode = "add_node"
        self.mode_label.config(text="Chế độ: Thêm đỉnh")
        self.canvas.config(cursor="plus")

    def set_add_edge_mode(self):
        """Chuyển sang chế độ thêm cạnh giữa hai đỉnh."""
        self.current_mode = "add_edge"
        self.mode_label.config(text="Chế độ: Thêm cạnh")
        self.canvas.config(cursor="plus")
        self.selected_node = None

    def set_delete_mode(self):
        """Chuyển sang chế độ xóa đỉnh hoặc cạnh."""
        self.current_mode = "delete"
        self.mode_label.config(text="Chế độ: Xóa")
        self.canvas.config(cursor="pirate")

    # ========== XỬ LÝ SỰ KIỆN ==========
    def handle_click(self, event):
        """
        Xử lý sự kiện click chuột trên canvas.

        Tùy theo chế độ hiện tại, xử lý thêm đỉnh, thêm cạnh,
        chọn đỉnh để kéo hoặc xóa đối tượng tại vị trí click.

        Tham số:
            event (tk.Event): Đối tượng sự kiện chuột.
        """
        x, y = event.x, event.y

        if self.current_mode == "add_node":
            self.create_node(x, y)

        elif self.current_mode == "add_edge":
            node = self.get_node_at_position(x, y)
            if node:
                if not self.selected_node:
                    self.selected_node = node
                    self.highlight_node(node)
                else:
                    if self.selected_node != node:
                        self.create_edge(self.selected_node, node)
                    self.reset_edge_mode()

        elif self.current_mode == "delete":
            self.delete_at_position(x, y)

        else:  # Chế độ select
            node = self.get_node_at_position(x, y)
            if node:
                self.dragging = True
                self.drag_node = node
                self.highlight_node(node)

    def handle_drag(self, event):
        """
        Xử lý kéo thả chuột để di chuyển đỉnh khi ở chế độ chọn.

        Tham số:
            event (tk.Event): Đối tượng sự kiện kéo chuột.
        """
        if self.dragging and self.drag_node and self.current_mode == "select":
            dx = event.x - self.nodes[self.drag_node][0]
            dy = event.y - self.nodes[self.drag_node][1]

            # Cập nhật vị trí đỉnh
            self.nodes[self.drag_node] = (event.x, event.y)

            # Di chuyển hình vẽ trên canvas
            self.canvas.moveto(f"node_{self.drag_node}",
                               event.x - self.node_radius,
                               event.y - self.node_radius)
            self.canvas.moveto(f"label_{self.drag_node}",
                               event.x - 10,
                               event.y - 10)

            # Cập nhật các cạnh liên quan
            self.update_edges_for_node(self.drag_node)

    def handle_release(self, event):
        """
        Xử lý thả chuột kết thúc thao tác kéo đỉnh.

        Tham số:
            event (tk.Event): Đối tượng sự kiện thả chuột.
        """
        if self.dragging and self.drag_node:
            self.canvas.itemconfig(f"node_{self.drag_node}", fill="lightblue")
        self.dragging = False
        self.drag_node = None

    # ========== THAO TÁC VỚI ĐỒ THỊ ==========
    def create_node(self, x, y):
        """
        Tạo đỉnh mới tại vị trí (x, y).

        Tham số:
            x (int): Tọa độ x trên canvas.
            y (int): Tọa độ y trên canvas.
        """
        node_id = f"n{len(self.nodes) + 1}"
        self.nodes[node_id] = (x, y)

        # Vẽ đỉnh
        self.canvas.create_oval(
            x - self.node_radius, y - self.node_radius,
            x + self.node_radius, y + self.node_radius,
            fill="lightblue", tags=f"node_{node_id}"
        )

        # Vẽ nhãn
        self.canvas.create_text(
            x, y, text=node_id, tags=f"label_{node_id}"
        )

    def create_edge(self, node1, node2):
        """
        Tạo cạnh nối giữa hai đỉnh node1 và node2.

        Nếu cạnh đã tồn tại hoặc node1 == node2 thì không tạo.

        Tham số:
            node1 (str): ID đỉnh đầu.
            node2 (str): ID đỉnh cuối.
        """
        if node1 != node2 and (node1, node2) not in self.edges and (node2, node1) not in self.edges:
            self.edges.append((node1, node2))
            self.draw_edge(node1, node2)

    def draw_edge(self, node1, node2):
        """
        Vẽ cạnh nối giữa hai đỉnh lên canvas.

        Tính toán điểm bắt đầu và kết thúc trên mép hình tròn đại diện đỉnh.

        Tham số:
            node1 (str): ID đỉnh đầu.
            node2 (str): ID đỉnh cuối.
        """
        x1, y1 = self.nodes[node1]
        x2, y2 = self.nodes[node2]

        # Tính toán điểm bắt đầu/kết thúc trên biên hình tròn
        angle = math.atan2(y2 - y1, x2 - x1)
        start_x = x1 + self.node_radius * math.cos(angle)
        start_y = y1 + self.node_radius * math.sin(angle)
        end_x = x2 - self.node_radius * math.cos(angle)
        end_y = y2 - self.node_radius * math.sin(angle)

        self.canvas.create_line(
            start_x, start_y, end_x, end_y,
            width=2, tags=f"edge_{node1}_{node2}"
        )

    def update_edges_for_node(self, node_id):
        """
        Cập nhật lại vị trí các cạnh có nối với đỉnh node_id khi đỉnh thay đổi vị trí.

        Tham số:
            node_id (str): ID đỉnh cần cập nhật cạnh.
        """
        for edge in [e for e in self.edges if node_id in e]:
            self.canvas.delete(f"edge_{edge[0]}_{edge[1]}")
            self.draw_edge(edge[0], edge[1])

    def delete_at_position(self, x, y):
        """
        Xóa đỉnh hoặc cạnh tại vị trí (x, y) nếu có.

        Ưu tiên xóa cạnh nếu click gần cạnh, nếu không thì xóa đỉnh.

        Tham số:
            x (int): Tọa độ x.
            y (int): Tọa độ y.
        """
        # Kiểm tra cạnh trước
        edge = self.get_edge_at_position(x, y)
        if edge:
            self.delete_edge(*edge)
            return

        # Nếu không click vào cạnh thì kiểm tra đỉnh
        node = self.get_node_at_position(x, y)
        if node:
            self.delete_node(node)

    def delete_node(self, node_id):
        """
        Xóa đỉnh và tất cả các cạnh liên quan tới đỉnh đó.

        Tham số:
            node_id (str): ID đỉnh cần xóa.
        """
        # Xóa các cạnh nối với đỉnh này
        for edge in [e for e in self.edges if node_id in e]:
            self.delete_edge(*edge)

        # Xóa đỉnh khỏi canvas
        self.canvas.delete(f"node_{node_id}")
        self.canvas.delete(f"label_{node_id}")

        # Xóa khỏi danh sách
        del self.nodes[node_id]

    def delete_edge(self, node1, node2):
        """
        Xóa cạnh nối giữa hai đỉnh node1 và node2.

        Tham số:
            node1 (str): ID đỉnh đầu.
            node2 (str): ID đỉnh cuối.
        """
        if (node1, node2) in self.edges:
            self.edges.remove((node1, node2))
        elif (node2, node1) in self.edges:
            self.edges.remove((node2, node1))

        self.canvas.delete(f"edge_{node1}_{node2}")
        self.canvas.delete(f"edge_{node2}_{node1}")

    # ========== TIỆN ÍCH ==========
    def get_node_at_position(self, x, y):
        """
        Tìm đỉnh tại vị trí (x, y).

        Trả về ID đỉnh nếu có, hoặc None nếu không có đỉnh nào gần.

        Tham số:
            x (int): Tọa độ x.
            y (int): Tọa độ y.

        Trả về:
            str hoặc None: ID đỉnh tìm được hoặc None.
        """
        for node_id, (nx, ny) in self.nodes.items():
            if math.hypot(x - nx, y - ny) <= self.node_radius:
                return node_id
        return None

    def get_edge_at_position(self, x, y, threshold=5):
        """
        Tìm cạnh gần vị trí (x, y) nhất trong khoảng cách threshold.

        Tham số:
            x (int): Tọa độ x.
            y (int): Tọa độ y.
            threshold (int): Khoảng cách tối đa để nhận diện cạnh.

        Trả về:
            tuple hoặc None: Cặp (node1, node2) của cạnh hoặc None nếu không tìm được.
        """
        for node1, node2 in self.edges:
            x1, y1 = self.nodes[node1]
            x2, y2 = self.nodes[node2]

            # Khoảng cách từ điểm đến đoạn thẳng
            dist = self.point_to_line_distance(x, y, x1, y1, x2, y2)
            if dist <= threshold:
                return (node1, node2)
        return None

    def point_to_line_distance(self, x, y, x1, y1, x2, y2):
        """
        Tính khoảng cách từ điểm (x, y) đến đoạn thẳng nối (x1, y1) - (x2, y2).

        Tham số:
            x, y (int): Tọa độ điểm.
            x1, y1, x2, y2 (int): Tọa độ hai đầu đoạn thẳng.

        Trả về:
            float: Khoảng cách từ điểm đến đoạn thẳng.
        """
        # Vector AB
        ABx = x2 - x1
        ABy = y2 - y1

        # Vector AP
        APx = x - x1
        APy = y - y1

        # Tích vô hướng
        dot = APx * ABx + APy * ABy
        AB_squared = ABx ** 2 + ABy ** 2

        # Tham số t
        t = max(0, min(1, dot / AB_squared))

        # Điểm gần nhất
        closest_x = x1 + t * ABx
        closest_y = y1 + t * ABy

        return math.hypot(x - closest_x, y - closest_y)

    def highlight_node(self, node_id):
        """
        Làm nổi bật đỉnh node_id trên canvas (thay đổi màu sắc).

        Tham số:
            node_id (str): ID đỉnh cần làm nổi bật.
        """
        self.canvas.itemconfig(f"node_{node_id}", fill="yellow")

    def reset_edge_mode(self):
        """
        Reset trạng thái chọn đỉnh khi đang ở chế độ thêm cạnh.
        """
        if self.selected_node:
            self.canvas.itemconfig(f"node_{self.selected_node}", fill="lightblue")
        self.selected_node = None

    # ========== TÍNH TOÁN ĐỒ THỊ ==========
    def check_connectivity(self):
        """
        Kiểm tra đồ thị có liên thông hay không.

        Sử dụng thuật toán BFS để duyệt các đỉnh.

        Hiển thị hộp thoại thông báo kết quả.
        """
        if not self.nodes:
            messagebox.showinfo("Thông báo", "Đồ thị trống!")
            return

        visited = set()
        queue = deque()

        # Bắt đầu từ đỉnh đầu tiên
        start_node = next(iter(self.nodes))
        queue.append(start_node)
        visited.add(start_node)

        while queue:
            current = queue.popleft()

            # Thêm các đỉnh kề chưa thăm
            for edge in self.edges:
                if current == edge[0] and edge[1] not in visited:
                    visited.add(edge[1])
                    queue.append(edge[1])
                elif current == edge[1] and edge[0] not in visited:
                    visited.add(edge[0])
                    queue.append(edge[0])

        if len(visited) == len(self.nodes):
            messagebox.showinfo("Kết quả", "Đồ thị LIÊN THÔNG")
        else:
            messagebox.showinfo("Kết quả",
                                f"Đồ thị KHÔNG LIÊN THÔNG\n({len(visited)}/{len(self.nodes)} đỉnh được kết nối)")

    def find_shortest_path(self):
        """
        Mở cửa sổ phụ để chọn 2 đỉnh rồi tìm đường đi ngắn nhất giữa chúng.

        Sử dụng BFS tìm đường.

        Nếu tìm được, sẽ làm nổi bật đường đi và hiển thị hộp thoại kết quả.
        """
        if len(self.nodes) < 2:
            messagebox.showinfo("Lỗi", "Cần ít nhất 2 đỉnh!")
            return

        # Tạo cửa sổ chọn đỉnh
        path_window = tk.Toplevel(self.root)
        path_window.title("Chọn đỉnh")

        tk.Label(path_window, text="Đỉnh bắt đầu:").pack()
        start_var = tk.StringVar(value=next(iter(self.nodes)))
        start_menu = tk.OptionMenu(path_window, start_var, *self.nodes.keys())
        start_menu.pack()

        tk.Label(path_window, text="Đỉnh kết thúc:").pack()
        end_var = tk.StringVar(value=next(iter(self.nodes)))
        end_menu = tk.OptionMenu(path_window, end_var, *self.nodes.keys())
        end_menu.pack()

        def execute():
            start = start_var.get()
            end = end_var.get()

            if start == end:
                messagebox.showinfo("Lỗi", "Chọn 2 đỉnh khác nhau!")
                return

            path = self.bfs_shortest_path(start, end)
            path_window.destroy()

            if path:
                self.highlight_path(path)
                messagebox.showinfo("Kết quả", f"Đường đi ngắn nhất:\n{' → '.join(path)}")
            else:
                messagebox.showinfo("Kết quả", "Không có đường đi!")

        tk.Button(path_window, text="Tìm đường", command=execute).pack(pady=10)

    def bfs_shortest_path(self, start, end):
        """
        Tìm đường đi ngắn nhất giữa hai đỉnh bằng thuật toán BFS.

        Tham số:
            start (str): ID đỉnh bắt đầu.
            end (str): ID đỉnh kết thúc.

        Trả về:
            list hoặc None: Danh sách ID đỉnh theo đường đi ngắn nhất hoặc None nếu không tìm được.
        """
        # Tạo danh sách kề
        adjacency = {node: [] for node in self.nodes}
        for a, b in self.edges:
            adjacency[a].append(b)
            adjacency[b].append(a)

        # BFS
        queue = deque([[start]])
        visited = set([start])

        while queue:
            path = queue.popleft()
            node = path[-1]

            if node == end:
                return path

            for neighbor in adjacency[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = list(path)
                    new_path.append(neighbor)
                    queue.append(new_path)

        return None

    def highlight_path(self, path):
        """Làm nổi bật đường đi trên đồ thị."""
        # Reset màu
        for node in self.nodes:
            self.canvas.itemconfig(f"node_{node}", fill="lightblue")
        for a, b in self.edges:
            self.canvas.itemconfig(f"edge_{a}_{b}", width=2, fill="black")

        # Tô màu đỉnh
        for node in path:
            self.canvas.itemconfig(f"node_{node}", fill="green")

        # Tô màu cạnh
        for i in range(len(path) - 1):
            a, b = path[i], path[i + 1]
            if (a, b) in self.edges:
                self.canvas.itemconfig(f"edge_{a}_{b}", width=4, fill="red")
            elif (b, a) in self.edges:
                self.canvas.itemconfig(f"edge_{b}_{a}", width=4, fill="red")

    # ========== LƯU/TẢI ĐỒ THỊ ==========
    def save_graph(self):
        """Lưu đồ thị vào file JSON."""
        if not self.nodes:
            messagebox.showinfo("Lỗi", "Không có gì để lưu!")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path:
            graph_data = {
                "nodes": {k: list(v) for k, v in self.nodes.items()},
                "edges": [list(e) for e in self.edges]
            }

            try:
                with open(file_path, 'w') as f:
                    json.dump(graph_data, f, indent=2)
                messagebox.showinfo("Thành công", "Lưu đồ thị thành công!")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể lưu file:\n{str(e)}")

    def load_graph(self):
        """Tải đồ thị từ file JSON."""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path:
            try:
                with open(file_path) as f:
                    data = json.load(f)

                self.clear_all()

                # Tải nodes
                for node_id, pos in data["nodes"].items():
                    self.nodes[node_id] = tuple(pos)
                    x, y = pos
                    self.canvas.create_oval(
                        x - self.node_radius, y - self.node_radius,
                        x + self.node_radius, y + self.node_radius,
                        fill="lightblue", tags=f"node_{node_id}"
                    )
                    self.canvas.create_text(
                        x, y, text=node_id, tags=f"label_{node_id}"
                    )

                # Tải edges
                self.edges = [tuple(edge) for edge in data["edges"]]
                for a, b in self.edges:
                    self.draw_edge(a, b)

                messagebox.showinfo("Thành công", "Tải đồ thị thành công!")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể tải file:\n{str(e)}")

    def clear_all(self):
        """Xóa toàn bộ đồ thị."""
        self.canvas.delete("all")
        self.nodes = {}
        self.edges = []
        self.dragging = False
        self.drag_node = None
        self.selected_node = None


if __name__ == "__main__":
    root = tk.Tk()
    app = GraphEditor(root)
    root.mainloop()