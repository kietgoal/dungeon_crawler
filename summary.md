# Dungeon Crawler 2D - Đồ án Cấu trúc Dữ liệu & Giải thuật

## Tổng quan

**Dungeon Crawler 2D** là một game nhập vai góc nhìn từ trên xuống (top-down) được viết bằng Python và thư viện Pygame. Điểm cốt lõi của đồ án là **Hệ thống Sinh Bản đồ Ngẫu nhiên (Procedural Map Generation)** và các thuật toán nền tảng của Khoa học Máy tính.

Mỗi khi người chơi bắt đầu một màn chơi mới, **100% bản đồ được máy tính tự động sinh ra** qua 3 giai đoạn thuật toán chặt chẽ. Không có bản đồ nào giống nhau.

---

## Cấu trúc Thuật toán

### 1. Binary Space Partitioning (BSP) — Cây Phân vùng Nhị phân

- **Mục đích**: Chia bản đồ lớn thành các vùng hình chữ nhật không chồng lấn, đảm bảo các căn phòng được bố trí gọn gàng.
- **Cách hoạt động**: Bắt đầu với toàn bộ màn hình là node gốc. Đệ quy cắt ngang/dọc cho đến khi đạt kích thước tối thiểu.
- **Độ phức tạp**: O(n) với n là số node.
- **Kết quả**: Các node lá chứa các căn phòng ngẫu nhiên.

### 2. Đồ thị (Graph) & Cây khung nhỏ nhất (MST - Kruskal)

- **Mục đích**: Kết nối tất cả các phòng bằng hành lang với tổng chiều dài ngắn nhất.
- **Đồ thị đầy đủ**: Tâm mỗi phòng là đỉnh, khoảng cách Euclidean giữa mọi cặp là cạnh. O(V²).
- **Kruskal + Union-Find**: Sắp xếp cạnh theo trọng số, dùng Disjoint Set để kiểm tra chu trình, chọn V-1 cạnh ngắn nhất. O(E log V).
- **Vòng lặp**: 10% cạnh bị loại được thêm lại để bản đồ có đường vòng, tránh nhàm chán.

### 3. A* Pathfinding — Tìm đường cho Quái vật

- **Mục đích**: Quái vật tìm đường đi ngắn nhất đến người chơi trong mê cung phức tạp.
- **Hàng đợi Ưu tiên (Min-Heap)**: Dùng `heapq` để quản lý Open Set.
- **Heuristic**: Khoảng cách Manhattan — ước lượng nhanh, chấp nhận được (admissible).
- **Tối ưu**: Chỉ tính lại đường mỗi 500ms hoặc khi người chơi di chuyển > 2 ô.
- **Độ phức tạp**: O(N log N) với N là số ô duyệt.

### 4. Field of View / Fog of War (BFS + Raycasting)

- **Mục đích**: Mô phỏng tầm nhìn — vùng ngoài bán kính hoặc sau tường bị tối.
- **BFS Loang**: Duyệt các ô sàn trong bán kính từ người chơi.
- **Raycasting (Bresenham)**: Kiểm tra tia nhìn từ người chơi đến từng ô — nếu có tường chắn, ô đó bị tối.
- **Độ phức tạp**: O(R²) với R = bán kính nhìn.

### 5. Chế độ Debug / Visualization

| Phím | Chức năng |
|------|-----------|
| `F1` | Vẽ các cạnh của MST (đường xanh) |
| `F2` | Vẽ ranh giới các node BSP (hình chữ nhật vàng) |
| `F3` | Vẽ đường đi A* của quái vật (đường hồng) |

---

## Gameplay

- **Điều khiển**: WASD / Phím mũi tên
- **Mục tiêu**: Sống sót càng lâu càng tốt. Quái vật truy đuổi bằng A*.
- **Permadeath**: Chết là mất hết, nhấn R để chơi lại với bản đồ mới.
- **Fog of War**: Bản đồ tối dần, người chơi khám phá đến đâu sáng đến đó.
- **Máu**: 3 máu. Chạm quái vật mất 1 máu.

---

## Công nghệ sử dụng

- **Python 3.14+**
- **Pygame 2.6.1** — đồ họa
- **heapq** — Priority Queue cho A*
- **math**, **random** — khoảng cách, ngẫu nhiên
- **pygame.Rect** — va chạm & vùng BSP

---

## Hướng dẫn chạy

```bash
pip install pygame
python main.py
```

Hoặc với script tự động (nếu pygame chưa cài trên hệ thống):

```bash
./run.sh
```

---

## Cấu trúc file

```
main.py           — Toàn bộ game (~700 dòng): DSA + Engine + Rendering
summary.md        — Mô tả đồ án (file này)
run.sh            — Script chạy với đường dẫn thư viện tùy chỉnh
```

---

## Độ phức tạp tổng thể

| Giai đoạn | Thuật toán | Độ phức tạp |
|-----------|-----------|-------------|
| Sinh phòng | BSP Tree | O(n) |
| Đồ thị | Complete Graph | O(V²) |
| Hành lang | Kruskal MST | O(E log V) |
| Tìm đường | A* + Min-Heap | O(N log N) |
| Tầm nhìn | BFS + Raycast | O(R²) |
| Toàn bộ pipeline | BSP → Graph → MST | O(V²) |

---

*Đồ án môn học Cấu trúc Dữ liệu và Giải thuật — 2025-2026*
