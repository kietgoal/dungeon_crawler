#!/usr/bin/env python3
"""
Dungeon Crawler 2D - Procedural Generation & DSA Visualization
==============================================================

Môn học: Cấu trúc Dữ liệu và Giải thuật (Data Structures & Algorithms)
Đề tài: 2D Procedural Dungeon Crawler với Binary Space Partitioning,
         Minimum Spanning Tree (Kruskal), A* Pathfinding, và Fog of War.

Sinh viên: Nguyễn Tuấn Kiệt - 25520957
Lớp: IT003.Q21.CTTN
Năm học: 2025-2026

Yêu cầu: pygame 2.0+, Python 3.10+
Cài đặt: pip install pygame
Chạy:    python main.py
"""

import pygame
import math
import random
import heapq
import os
from typing import Optional

# =============================================================================
#  CẤU HÌNH (CONFIGURATION)
# =============================================================================
SCREEN_WIDTH = 1366
SCREEN_HEIGHT = 768
TILE_SIZE = 32
MAP_COLS = SCREEN_WIDTH // TILE_SIZE    # 42
MAP_ROWS = SCREEN_HEIGHT // TILE_SIZE   # 24

FPS = 60
FOV_RADIUS = 8
ENEMY_SPEED = 3.375  # tiles per second
PLAYER_SPEED = 6.75
ENEMY_RECALC_INTERVAL = 150  # ms between path recalculations
ENEMY_DETECTION_RANGE = 6   # tiles - enemy starts chasing when player is within this range

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GRAY = (30, 30, 30)
GRAY = (80, 80, 80)
LIGHT_GRAY = (180, 180, 180)
WALL_COLOR = (60, 60, 60)
FLOOR_COLOR = (200, 200, 200)
PLAYER_COLOR = (50, 150, 255)
ENEMY_COLOR = (220, 50, 50)
DEBUG_MST_COLOR = (0, 255, 0)
DEBUG_BSP_COLOR = (255, 255, 0)
DEBUG_PATH_COLOR = (255, 100, 255)
VISIBLE_COLOR = (255, 255, 255, 0)       # fully transparent
EXPLORED_COLOR = (0, 0, 0, 160)          # semi-transparent dark
HIDDEN_COLOR = (0, 0, 0, 255)            # fully dark
HEALTH_BAR_COLOR = (50, 220, 50)
HEALTH_BG_COLOR = (100, 30, 30)
UI_BG_COLOR = (20, 20, 20, 200)

TILE_FLOOR = 0
TILE_WALL = 1


# =============================================================================
#  THUẬT TOÁN & CẤU TRÚC DỮ LIỆU (DSA CORE - Decoupled from Pygame)
# =============================================================================

# ------------------------------------------------------------
#  BINARY SPACE PARTITIONING (BSP Tree)
# ------------------------------------------------------------
class BSPNode:
    """
    Một node trong cây BSP (Binary Space Partitioning).

    Chức năng: Đại diện cho một vùng hình chữ nhật trong bản đồ.
    Node có thể được chia (split) thành 2 node con bằng đường cắt
    ngang hoặc dọc. Node lá (không có con) sẽ chứa một căn phòng.

    Time Complexity:
        - split(): O(1) để cắt node cha thành 2 node con.
        - create_room(): O(1) để tạo phòng ngẫu nhiên trong node.
        - get_leaves(): O(n) với n là số node trong cây.
    """
    def __init__(self, x: int, y: int, w: int, h: int):
        self.rect = pygame.Rect(x, y, w, h)
        self.left: Optional[BSPNode] = None
        self.right: Optional[BSPNode] = None
        self.room: Optional[pygame.Rect] = None

    def split(self, min_size: int = 7) -> bool:
        """
        Chia node thành 2 node con.
        Chọn ngẫu nhiên cắt ngang hoặc dọc.
        Args:
            min_size: Kích thước tối thiểu cho node con.
        Returns:
            True nếu split thành công, False nếu quá nhỏ.
        Time: O(1)
        Space: O(1)
        """
        w, h = self.rect.w, self.rect.h
        if w < min_size * 2 or h < min_size * 2:
            return False

        split_h = random.choice([True, False])
        if w > h and w / h >= 1.25:
            split_h = False
        elif h > w and h / w >= 1.25:
            split_h = True

        max_val = (w if not split_h else h) - min_size
        if max_val <= min_size:
            return False
        split_pos = random.randint(min_size, max_val)

        if split_h:
            self.left = BSPNode(self.rect.x, self.rect.y, w, split_pos)
            self.right = BSPNode(self.rect.x, self.rect.y + split_pos, w, h - split_pos)
        else:
            self.left = BSPNode(self.rect.x, self.rect.y, split_pos, h)
            self.right = BSPNode(self.rect.x + split_pos, self.rect.y, w - split_pos, h)
        return True

    def create_room(self) -> None:
        """
        Tạo một căn phòng ngẫu nhiên bên trong node.
        Phòng là hình chữ nhật nhỏ hơn, nằm lọt trong node với padding 1 ô.
        Time: O(1)
        """
        if self.left or self.right:
            if self.left:
                self.left.create_room()
            if self.right:
                self.right.create_room()
        else:
            pad = 1
            rw = random.randint(4, max(4, self.rect.w - pad * 2))
            rh = random.randint(4, max(4, self.rect.h - pad * 2))
            rx = self.rect.x + random.randint(pad, max(pad, self.rect.w - rw - pad))
            ry = self.rect.y + random.randint(pad, max(pad, self.rect.h - rh - pad))
            self.room = pygame.Rect(rx, ry, rw, rh)

    def get_leaves(self) -> list['BSPNode']:
        """
        Duyệt cây và trả về danh sách các node lá (không có con).
        Time: O(n) với n là số node trong cây.
        """
        if not self.left and not self.right:
            return [self]
        leaves = []
        if self.left:
            leaves.extend(self.left.get_leaves())
        if self.right:
            leaves.extend(self.right.get_leaves())
        return leaves

    def get_all_rooms(self) -> list[pygame.Rect]:
        """
        Lấy danh sách tất cả các phòng từ cây (các node lá có room).
        Time: O(n)
        """
        rooms = []
        if self.left or self.right:
            if self.left:
                rooms.extend(self.left.get_all_rooms())
            if self.right:
                rooms.extend(self.right.get_all_rooms())
        elif self.room:
            rooms.append(self.room)
        return rooms


class BSPTree:
    """
    Cây Binary Space Partitioning - quản lý toàn bộ quá trình
    phân chia không gian bản đồ.

    Time Complexity tổng thể:
        - Xây dựng cây: O(n) với n là số lần split.
        - Tạo phòng: O(n).
    Space Complexity: O(n) lưu trữ các node.
    """
    def __init__(self, x: int, y: int, w: int, h: int, depth: int = 6):
        self.root = BSPNode(x, y, w, h)
        self._build(depth)

    def _build(self, depth: int) -> None:
        """
        Xây dựng cây BSP bằng cách split đệ quy đến độ sâu cho trước.
        Args:
            depth: Số lần split tối đa (độ sâu của cây).
        Time: O(2^depth) ~ O(n)
        """
        nodes = [self.root]
        for _ in range(depth):
            next_nodes = []
            for node in nodes:
                if node.split():
                    next_nodes.append(node.left)
                    next_nodes.append(node.right)
                else:
                    next_nodes.append(node)
            nodes = next_nodes
        self.root.create_room()

    def get_rooms(self) -> list[pygame.Rect]:
        """
        Lấy danh sách các phòng từ tất cả node lá.
        Returns:
            list[pygame.Rect]: Danh sách các phòng.
        Time: O(n)
        """
        return self.root.get_all_rooms()

    def get_leaves(self) -> list[BSPNode]:
        """
        Lấy tất cả node lá (dùng cho debug F2).
        Time: O(n)
        """
        return self.root.get_leaves()


# ------------------------------------------------------------
#  ĐỒ THỊ (GRAPH)
# ------------------------------------------------------------
class Graph:
    """
    Đồ thị vô hướng có trọng số dùng để biểu diễn kết nối giữa các phòng.

    Mỗi đỉnh (vertex) là tâm của một căn phòng.
    Mỗi cạnh (edge) có trọng số là khoảng cách Euclidean giữa 2 phòng.

    Time Complexity:
        - add_vertex(): O(1)
        - add_edge(): O(1)
        - get_edges(): O(E) với E là số cạnh.
    Space Complexity: O(V + E)
    """
    def __init__(self):
        self.vertices: dict[int, tuple[float, float]] = {}
        self.edges: list[tuple[int, int, float]] = []

    def add_vertex(self, vid: int, pos: tuple[float, float]) -> None:
        """
        Thêm một đỉnh mới vào đồ thị.
        Args:
            vid: ID của đỉnh (số thứ tự phòng).
            pos: Tọa độ (x, y) của tâm phòng.
        Time: O(1)
        """
        self.vertices[vid] = pos

    def add_edge(self, v1: int, v2: int, weight: float) -> None:
        """
        Thêm cạnh vô hướng giữa 2 đỉnh.
        Args:
            v1, v2: ID của 2 đỉnh.
            weight: Trọng số (khoảng cách).
        Time: O(1)
        """
        self.edges.append((v1, v2, weight))

    def get_edges(self) -> list[tuple[int, int, float]]:
        """
        Trả về danh sách tất cả các cạnh.
        Time: O(E)
        """
        return self.edges

    def get_vertex_positions(self) -> dict[int, tuple[float, float]]:
        """
        Trả về dict vị trí các đỉnh.
        Time: O(V)
        """
        return dict(self.vertices)

    def build_complete_from_rooms(self, rooms: list[pygame.Rect]) -> None:
        """
        Xây dựng đồ thị đầy đủ từ danh sách phòng.
        Mỗi phòng là 1 đỉnh, cạnh nối mọi cặp đỉnh với trọng số
        là khoảng cách Euclidean giữa tâm 2 phòng.

        Args:
            rooms: Danh sách các phòng (pygame.Rect).

        Time Complexity: O(V^2) với V = số phòng.
            - Với V phòng, có V*(V-1)/2 cạnh ~ O(V^2).
        """
        centers = []
        for i, room in enumerate(rooms):
            cx = room.centerx
            cy = room.centery
            self.add_vertex(i, (cx, cy))
            centers.append((i, cx, cy))

        for i in range(len(centers)):
            for j in range(i + 1, len(centers)):
                vid1, x1, y1 = centers[i]
                vid2, x2, y2 = centers[j]
                dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
                self.add_edge(vid1, vid2, dist)


# ------------------------------------------------------------
#  DISJOINT SET (UNION-FIND)
# ------------------------------------------------------------
class UnionFind:
    """
    Cấu trúc Disjoint Set (Union-Find) dùng trong thuật toán Kruskal.

    Sử dụng:
        - Path Compression trong find() để tối ưu.
        - Union by Rank trong union() để giữ cây cân bằng.

    Time Complexity:
        - find(): O(alpha(n)) ~ O(1) với alpha là hàm Ackermann ngược.
        - union(): O(alpha(n)) ~ O(1).
    Space Complexity: O(n)
    """
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        """
        Tìm gốc (root) của tập chứa x.
        Sử dụng Path Compression: nén đường đi để tối ưu các lần gọi sau.

        Args:
            x: Phần tử cần tìm.
        Returns:
            int: Gốc của tập chứa x.
        Time: O(alpha(n)) amortized.
        """
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: int, y: int) -> bool:
        """
        Hợp nhất 2 tập chứa x và y.
        Sử dụng Union by Rank: gắn cây thấp vào cây cao.

        Args:
            x, y: 2 phần tử cần hợp nhất.
        Returns:
            True nếu 2 tập được hợp nhất, False nếu đã cùng tập.
        Time: O(alpha(n)) amortized.
        """
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        if self.rank[rx] < self.rank[ry]:
            self.parent[rx] = ry
        elif self.rank[rx] > self.rank[ry]:
            self.parent[ry] = rx
        else:
            self.parent[ry] = rx
            self.rank[rx] += 1
        return True


# ------------------------------------------------------------
#  MINIMUM SPANNING TREE (Kruskal's Algorithm)
# ------------------------------------------------------------
class KruskalMST:
    """
    Thuật toán Kruskal tìm Cây khung nhỏ nhất (Minimum Spanning Tree).

    Ý tưởng:
        1. Sắp xếp tất cả các cạnh theo trọng số tăng dần.
        2. Dùng Union-Find để kiểm tra chu trình.
        3. Thêm cạnh vào MST nếu 2 đầu cạnh thuộc 2 tập khác nhau.

    Sau khi tìm MST, có thể thêm lại 10% cạnh bị loại để tạo vòng lặp
    (giúp bản đồ không bị dạng cây đơn thuần).

    Time Complexity: O(E log V)
        - Sắp xếp cạnh: O(E log E) ~ O(E log V) vì log E ~ log V.
        - Duyệt cạnh: O(E * alpha(V)) ~ O(E).
    Space Complexity: O(V + E)
    """
    @staticmethod
    def compute(
        vertex_count: int,
        edges: list[tuple[int, int, float]],
        loop_chance: float = 0.1
    ) -> list[tuple[int, int, float]]:
        """
        Tìm MST và trả về danh sách cạnh kết nối tất cả các đỉnh.

        Args:
            vertex_count: Số lượng đỉnh.
            edges: Danh sách cạnh (v1, v2, weight).
            loop_chance: Xác suất thêm lại cạnh bị loại (0.1 = 10%).

        Returns:
            list[tuple]: Danh sách cạnh của MST + optional loops.

        Time: O(E log V)
        Space: O(V + E)
        """
        sorted_edges = sorted(edges, key=lambda e: e[2])
        uf = UnionFind(vertex_count)
        mst_edges: list[tuple[int, int, float]] = []
        discarded: list[tuple[int, int, float]] = []

        for v1, v2, w in sorted_edges:
            if uf.find(v1) != uf.find(v2):
                uf.union(v1, v2)
                mst_edges.append((v1, v2, w))
            else:
                discarded.append((v1, v2, w))

        for v1, v2, w in discarded:
            if random.random() < loop_chance:
                mst_edges.append((v1, v2, w))

        return mst_edges


# ------------------------------------------------------------
#  A* PATHFINDING
# ------------------------------------------------------------
class AStar:
    """
    Thuật toán A* (A-Star) tìm đường đi ngắn nhất trên lưới.

    Đặc điểm:
        - Hàng đợi ưu tiên (Min-Heap) dùng heapq cho Open Set.
        - Heuristic: Khoảng cách Manhattan.
        - Chỉ di chuyển 4 hướng (lên, xuống, trái, phải).

    Time Complexity: O(E log V) = O(N log N) với N là số ô lưới.
        - Mỗi ô được duyệt tối đa 1 lần.
        - Mỗi lần thêm vào heap: O(log N).
    Space Complexity: O(N) với N = số ô lưới.
    """
    def __init__(self, grid: list[list[int]]):
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0])

    @staticmethod
    def heuristic(a: tuple[int, int], b: tuple[int, int]) -> int:
        """
        Hàm Heuristic: Khoảng cách Manhattan.
        Dùng để ước lượng khoảng cách từ node hiện tại đến đích.

        Args:
            a: (x, y) tọa độ hiện tại.
            b: (x, y) tọa độ đích.

        Returns:
            int: |x1 - x2| + |y1 - y2|

        Time: O(1)
        """
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def find_path(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
        max_nodes: int = 500
    ) -> list[tuple[int, int]]:
        """
        Tìm đường đi từ start đến goal trên lưới.

        Args:
            start: (x, y) tọa độ bắt đầu (tile).
            goal: (x, y) tọa độ đích (tile).
            max_nodes: Giới hạn số node duyệt để tránh treo game.

        Returns:
            list[tuple]: Đường đi dạng list các (x, y) từ start đến goal.
                         Trả về [] nếu không tìm thấy đường.

        Time: O(N log N) với N = số ô duyệt.
        """
        if not self._is_walkable(start[0], start[1]):
            return []
        if not self._is_walkable(goal[0], goal[1]):
            return []

        # Open Set: priority queue (Min-Heap) chứa (f_score, counter, (x, y))
        open_set: list[tuple[float, int, tuple[int, int]]] = []
        counter = 0

        heapq.heappush(open_set, (0.0, counter, start))
        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score: dict[tuple[int, int], float] = {start: 0.0}
        f_score: dict[tuple[int, int], float] = {start: self.heuristic(start, goal)}

        nodes_visited = 0
        while open_set and nodes_visited < max_nodes:
            _, _, current = heapq.heappop(open_set)
            nodes_visited += 1

            if current == goal:
                return self._reconstruct_path(came_from, current)

            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = current[0] + dx, current[1] + dy
                neighbor = (nx, ny)
                if not self._is_walkable(nx, ny):
                    continue

                tentative_g = g_score[current] + 1.0
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = tentative_g + self.heuristic(neighbor, goal)
                    f_score[neighbor] = f
                    counter += 1
                    heapq.heappush(open_set, (f, counter, neighbor))

        return []

    def _is_walkable(self, x: int, y: int) -> bool:
        """
        Kiểm tra ô (x, y) có thể đi được không.
        Time: O(1)
        """
        return 0 <= y < self.rows and 0 <= x < self.cols and self.grid[y][x] == TILE_FLOOR

    @staticmethod
    def _reconstruct_path(
        came_from: dict[tuple[int, int], tuple[int, int]],
        current: tuple[int, int]
    ) -> list[tuple[int, int]]:
        """
        Tái tạo đường đi từ dict came_from.
        Time: O(L) với L = độ dài đường đi.
        """
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path


# ------------------------------------------------------------
#  FIELD OF VIEW (FOG OF WAR) - BFS + Raycasting
# ------------------------------------------------------------
class FogOfWar:
    """
    Hệ thống Tầm nhìn (Fog of War) dùng BFS kết hợp kiểm tra tia nhìn.

    Sử dụng BFS:
        - Từ vị trí người chơi, BFS loang trên các ô sàn (floor).
        - Mỗi ô trong bán kính được kiểm tra tia nhìn (raycasting)
          để xác định xem có bị tường chắn không.
        - Ô đã thấy trước đây nhưng không còn trong tầm nhìn
          được đánh dấu là "explored" (đã khám phá).

    Time Complexity: O(R^2) với R = FOV_RADIUS.
        - BFS duyệt tối đa O(R^2) ô.
        - Mỗi ô kiểm tra tia: O(R).
        - Tổng: O(R^3). Với R nhỏ (8-12), chạy rất nhanh.
    Space Complexity: O(M * N) với M, N là kích thước lưới.
    """
    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self.visible: set[tuple[int, int]] = set()
        self.explored: set[tuple[int, int]] = set()

    def compute_visibility(
        self,
        player_pos: tuple[int, int],
        grid: list[list[int]],
        radius: int
    ) -> None:
        """
        Tính toán tầm nhìn từ vị trí người chơi.

        Dùng BFS để loang trên các ô sàn, kết hợp raycasting
        để kiểm tra xem tia nhìn từ player có bị chặn bởi tường không.

        Args:
            player_pos: (x, y) tọa độ người chơi (tile).
            grid: Lưới bản đồ (0 = floor, 1 = wall).
            radius: Bán kính nhìn (tile).

        Time: O(R^2) với kiểm tra tia O(R) mỗi ô ~ O(R^3).
              Trong thực tế với R=8, chỉ duyệt ~200 ô, rất nhanh.
        """
        self.visible.clear()
        px, py = player_pos

        # BFS loang từ player
        visited: set[tuple[int, int]] = set()
        queue: list[tuple[int, int, int]] = [(px, py, 0)]
        visited.add((px, py))

        while queue:
            x, y, dist = queue.pop(0)
            if dist > radius:
                continue

            # Kiểm tra tia nhìn từ player đến (x, y)
            if self._has_line_of_sight(px, py, x, y, grid):
                self.visible.add((x, y))
                self.explored.add((x, y))

            # Thêm các ô lân cận (4 hướng)
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in visited:
                    if 0 <= ny < self.rows and 0 <= nx < self.cols:
                        visited.add((nx, ny))
                        queue.append((nx, ny, dist + 1))

    @staticmethod
    def _has_line_of_sight(
        x0: int, y0: int, x1: int, y1: int,
        grid: list[list[int]]
    ) -> bool:
        """
        Kiểm tra xem có tia nhìn từ (x0, y0) đến (x1, y1) không.
        Dùng thuật toán Bresenham's Line để dò tia.

        Args:
            x0, y0: Tọa độ bắt đầu (người chơi).
            x1, y1: Tọa độ kết thúc.
            grid: Lưới bản đồ.

        Returns:
            True nếu có tia nhìn (không bị tường chặn).

        Time: O(max(|dx|, |dy|)) ~ O(R).
        """
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        cx, cy = x0, y0

        while True:
            if cx == x1 and cy == y1:
                return True
            if grid[cy][cx] == TILE_WALL:
                return False
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                cx += sx
            if e2 <= dx:
                err += dx
                cy += sy


# =============================================================================
#  MAP GENERATION PIPELINE (Orchestrator)
# =============================================================================
class DungeonMap:
    """
    Điều phối toàn bộ quy trình sinh bản đồ 3 bước:
        Bước 1: BSP Tree -> danh sách phòng.
        Bước 2: Graph (đồ thị đầy đủ từ tâm phòng).
        Bước 3: Kruskal MST + hành lang (corridors).

    Time Complexity tổng thể: O(V^2 + E log V) với V = số phòng.
        - BSP: O(n) với n là số node.
        - Complete Graph: O(V^2).
        - MST: O(E log V) = O(V^2 log V).
        - Corridors: O(V) đường hầm.
    Space Complexity: O(MAP_ROWS * MAP_COLS) cho lưới + O(V^2) cho đồ thị.
    """
    def __init__(self):
        self.grid: list[list[int]] = [[TILE_WALL] * MAP_COLS for _ in range(MAP_ROWS)]
        self.rooms: list[pygame.Rect] = []
        self.mst_edges: list[tuple[int, int, float]] = []
        self.graph_edges: list[tuple[int, int, float]] = []
        self.room_centers: list[tuple[int, int]] = []
        self.bsp_tree: Optional[BSPTree] = None
        self.staircase_tile: Optional[tuple[int, int]] = None

    def generate(self, bsp_depth: int = 6) -> None:
        """
        Sinh bản đồ hoàn chỉnh qua 3 bước.

        Args:
            bsp_depth: Độ sâu của cây BSP (số lần split).

        Time: O(V^2 + E log V)
        """
        self.grid = [[TILE_WALL] * MAP_COLS for _ in range(MAP_ROWS)]
        self.rooms.clear()
        self.mst_edges.clear()
        self.graph_edges.clear()
        self.room_centers.clear()

        # Bước 1: BSP Tree
        self.bsp_tree = BSPTree(0, 0, MAP_COLS, MAP_ROWS, depth=bsp_depth)
        self.rooms = self.bsp_tree.get_rooms()

        for room in self.rooms:
            self._carve_room(room)

        # Bước 2: Graph
        graph = Graph()
        graph.build_complete_from_rooms(self.rooms)
        self.graph_edges = graph.get_edges()

        # Bước 3: Kruskal MST
        self.mst_edges = KruskalMST.compute(len(self.rooms), self.graph_edges)

        # Đào hành lang (corridors)
        for v1, v2, _ in self.mst_edges:
            x1 = int(self.rooms[v1].centerx)
            y1 = int(self.rooms[v1].centery)
            x2 = int(self.rooms[v2].centerx)
            y2 = int(self.rooms[v2].centery)
            self._carve_corridor(x1, y1, x2, y2)

        # Lưu tâm phòng
        self.room_centers = [(int(r.centerx), int(r.centery)) for r in self.rooms]

        # Xoá ngã cụt
        self._remove_dead_ends()

        # Chọn phòng ngẫu nhiên cho cầu thang
        if self.rooms:
            room = random.choice(self.rooms)
            self.staircase_tile = (int(room.centerx), int(room.centery))

    def _carve_room(self, room: pygame.Rect) -> None:
        """
        Đào (carve) một căn phòng trên lưới: đặt tất cả ô trong phòng
        thành TILE_FLOOR.

        Args:
            room: Hình chữ nhật của phòng.
        Time: O(w * h) với w, h là kích thước phòng.
        """
        for y in range(room.top, room.bottom):
            for x in range(room.left, room.right):
                if 0 <= y < MAP_ROWS and 0 <= x < MAP_COLS:
                    self.grid[y][x] = TILE_FLOOR

    def _carve_corridor(self, x1: int, y1: int, x2: int, y2: int) -> None:
        """
        Đào hành lang hình chữ L nối 2 điểm (x1, y1) và (x2, y2).
        Hành lang rộng 2 ô để player có thể né enemy.
        """
        if random.random() < 0.5:
            for x in range(min(x1, x2), max(x1, x2) + 1):
                for dy in range(2):
                    yy = y1 + dy
                    if 0 <= yy < MAP_ROWS and 0 <= x < MAP_COLS:
                        self.grid[yy][x] = TILE_FLOOR
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for dx in range(2):
                    xx = x2 + dx
                    if 0 <= y < MAP_ROWS and 0 <= xx < MAP_COLS:
                        self.grid[y][xx] = TILE_FLOOR
        else:
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for dx in range(2):
                    xx = x1 + dx
                    if 0 <= y < MAP_ROWS and 0 <= xx < MAP_COLS:
                        self.grid[y][xx] = TILE_FLOOR
            for x in range(min(x1, x2), max(x1, x2) + 1):
                for dy in range(2):
                    yy = y2 + dy
                    if 0 <= yy < MAP_ROWS and 0 <= x < MAP_COLS:
                        self.grid[yy][x] = TILE_FLOOR

    def _remove_dead_ends(self) -> None:
        """
        Xoá các ngã cụt (dead end) trên bản đồ.
        Lặp lại cho đến khi không còn ô sàn nào chỉ có 1 lối vào.
        """
        changed = True
        while changed:
            changed = False
            for y in range(1, MAP_ROWS - 1):
                for x in range(1, MAP_COLS - 1):
                    if self.grid[y][x] == TILE_FLOOR:
                        count = 0
                        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                            if self.grid[y + dy][x + dx] == TILE_FLOOR:
                                count += 1
                        if count <= 1:
                            self.grid[y][x] = TILE_WALL
                            changed = True

    def find_random_floor(self) -> tuple[int, int]:
        """
        Tìm một ô sàn (floor) ngẫu nhiên trên bản đồ.
        Dùng để spawn player và enemy.

        Returns:
            (x, y) tọa độ ô sàn.
        Time: O(1) trong thực tế do tìm trên danh sách các ô sàn,
              nhưng có thể mất nhiều lần thử nếu bản đồ nhỏ.
        """
        for _ in range(1000):
            x = random.randint(1, MAP_COLS - 2)
            y = random.randint(1, MAP_ROWS - 2)
            if self.grid[y][x] == TILE_FLOOR:
                return (x, y)
        return (1, 1)


# =============================================================================
#  ENTITIES (Player & Enemy)
# =============================================================================
class Player:
    """
    Người chơi: di chuyển bằng WASD/Arrow, tương tác với bản đồ.

    Time Complexity các phương thức: O(1).
    """
    def __init__(self, x: int, y: int):
        self.tile_x: float = float(x)
        self.tile_y: float = float(y)
        self.speed: float = PLAYER_SPEED
        self.alive: bool = True
        self.health: int = 3
        self.max_health: int = 3
        self.invincible_until: int = 0
        self.last_dx: float = 0.0
        self.last_dy: float = 0.0
        self.direction: str = "front"

    def get_tile_pos(self) -> tuple[int, int]:
        """Trả về tọa độ tile hiện tại. Time: O(1)"""
        return (int(self.tile_x), int(self.tile_y))

    def get_pixel_rect(self) -> pygame.Rect:
        """Trả về rect pixel để vẽ. Time: O(1)"""
        return pygame.Rect(
            int(self.tile_x * TILE_SIZE),
            int(self.tile_y * TILE_SIZE),
            TILE_SIZE, TILE_SIZE
        )

    def move(self, dx: float, dy: float, grid: list[list[int]]) -> bool:
        """
        Di chuyển người chơi, kiểm tra va chạm tường.

        Args:
            dx, dy: Hướng di chuyển (1, -1, hoặc 0).
            grid: Lưới bản đồ.

        Returns:
            True nếu di chuyển thành công.

        Time: O(1)
        """
        if not self.alive:
            return False

        self.last_dx = dx
        self.last_dy = dy
        # Sprite rotation: S→right, A→front, D→left, W→back
        if dy < 0:
            self.direction = "back"
        elif dy > 0:
            self.direction = "right"
        elif dx < 0:
            self.direction = "front"
        elif dx > 0:
            self.direction = "left"

        new_x = self.tile_x + dx * self.speed / FPS
        new_y = self.tile_y + dy * self.speed / FPS

        nx, ny = int(new_x), int(new_y)
        if 0 <= ny < MAP_ROWS and 0 <= nx < MAP_COLS:
            if grid[ny][nx] == TILE_FLOOR:
                self.tile_x = new_x
                self.tile_y = new_y
                return True

        # Thử từng trục riêng lẻ (slide along wall)
        nx = int(self.tile_x + dx * self.speed / FPS)
        if 0 <= int(self.tile_y) < MAP_ROWS and 0 <= nx < MAP_COLS:
            if grid[int(self.tile_y)][nx] == TILE_FLOOR:
                self.tile_x += dx * self.speed / FPS

        ny = int(self.tile_y + dy * self.speed / FPS)
        if 0 <= ny < MAP_ROWS and 0 <= int(self.tile_x) < MAP_COLS:
            if grid[ny][int(self.tile_x)] == TILE_FLOOR:
                self.tile_y += dy * self.speed / FPS

        return False

    def take_damage(self, amount: int = 1, current_time: int = 0) -> None:
        if current_time < self.invincible_until:
            return
        self.health -= amount
        if self.health <= 0:
            self.alive = False
            self.health = 0
        else:
            self.invincible_until = current_time + 1000


class Enemy:
    """
    Quái vật: di chuyển về phía người chơi bằng A* Pathfinding.

    Tối ưu: Chỉ tính lại đường đi mỗi ENEMY_RECALC_INTERVAL ms,
    hoặc khi người chơi di chuyển > 2 tiles so với lần tính cuối.

    Time Complexity:
        - update(): O(1) nếu không tính lại path.
        - Tính lại path: O(N log N) với N là số ô trong BFS.
    """
    def __init__(self, x: int, y: int):
        self.tile_x: float = float(x)
        self.tile_y: float = float(y)
        self.speed: float = ENEMY_SPEED
        self.path: list[tuple[int, int]] = []
        self.path_index: int = 0
        self.last_path_time: int = 0
        self.last_player_pos: tuple[int, int] = (-1, -1)
        self.direction: str = "front"
        self.moving: bool = True
        self.wander_target: Optional[tuple[int, int]] = None
        self.wander_path_time: int = 0
        self.redirect_until: int = 0
        self.last_tile_pos: tuple[int, int] = (-1, -1)
        self.stuck_time: int = 0

    def get_tile_pos(self) -> tuple[int, int]:
        """Trả về tọa độ tile. Time: O(1)"""
        return (int(self.tile_x), int(self.tile_y))

    def get_pixel_rect(self) -> pygame.Rect:
        """Trả về rect pixel. Time: O(1)"""
        return pygame.Rect(
            int(self.tile_x * TILE_SIZE),
            int(self.tile_y * TILE_SIZE),
            TILE_SIZE, TILE_SIZE
        )

    def update(
        self,
        player_pos: tuple[int, int],
        grid: list[list[int]],
        current_time: int,
        is_chaser: bool = False
    ) -> None:
        my_pos = self.get_tile_pos()
        px, py = player_pos

        if self.stuck_time > 0 and current_time - self.stuck_time > 500:
            self.path = []
            self.path_index = 0
            self.wander_target = None
            self.wander_path_time = 0
            self.redirect_until = current_time + 800
            self.stuck_time = current_time
            self.last_tile_pos = my_pos
        elif my_pos == self.last_tile_pos:
            if self.stuck_time == 0:
                self.stuck_time = current_time
        else:
            self.last_tile_pos = my_pos
            self.stuck_time = 0

        if is_chaser and current_time >= self.redirect_until:
            need_recalc = False
            if not self.path or self.path_index >= len(self.path):
                need_recalc = True
            elif current_time - self.last_path_time > ENEMY_RECALC_INTERVAL:
                need_recalc = True
            elif self.path_index < len(self.path):
                tx, ty = self.path[self.path_index]
                if not (0 <= ty < len(grid) and 0 <= tx < len(grid[0]) and grid[ty][tx] == TILE_FLOOR):
                    need_recalc = True

            if need_recalc:
                astar = AStar(grid)
                self.path = astar.find_path(my_pos, player_pos)
                self.path_index = 0
                while self.path_index < len(self.path) and self.path[self.path_index] == my_pos:
                    self.path_index += 1
                self.last_path_time = current_time
                self.last_player_pos = player_pos

            if not self.path or self.path_index >= len(self.path):
                dx = px - self.tile_x
                dy = py - self.tile_y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > 0.1:
                    if abs(dx) > abs(dy):
                        self.direction = "left" if dx < 0 else "right"
                    else:
                        self.direction = "back" if dy < 0 else "front"
                    step = self.speed / FPS
                    self.tile_x += (dx / dist) * step
                    self.tile_y += (dy / dist) * step
                return

            self._follow_path()
        else:
            if (self.wander_target is None or
                my_pos == self.wander_target or
                current_time - self.wander_path_time > 4000):
                for _ in range(50):
                    rx = random.randint(2, len(grid[0]) - 3)
                    ry = random.randint(2, len(grid) - 3)
                    if grid[ry][rx] == TILE_FLOOR:
                        self.wander_target = (rx, ry)
                        break
                if self.wander_target and my_pos != self.wander_target:
                    astar = AStar(grid)
                    self.path = astar.find_path(my_pos, self.wander_target)
                    self.path_index = 0
                    while self.path_index < len(self.path) and self.path[self.path_index] == my_pos:
                        self.path_index += 1
                    self.wander_path_time = current_time
                else:
                    self.wander_path_time = current_time

            if not self.path or self.path_index >= len(self.path):
                if self.wander_target:
                    dx = self.wander_target[0] - self.tile_x
                    dy = self.wander_target[1] - self.tile_y
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist > 0.1:
                        if abs(dx) > abs(dy):
                            self.direction = "left" if dx < 0 else "right"
                        else:
                            self.direction = "back" if dy < 0 else "front"
                        step = self.speed / FPS
                        self.tile_x += (dx / dist) * step
                        self.tile_y += (dy / dist) * step
                return

            self._follow_path()

    def _follow_path(self) -> None:
        while self.path_index < len(self.path):
            target = self.path[self.path_index]
            tx, ty = target
            dx = tx - self.tile_x
            dy = ty - self.tile_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 0.1:
                self.path_index += 1
            else:
                break

        if self.path_index >= len(self.path):
            return

        target = self.path[self.path_index]
        tx, ty = target
        dx = tx - self.tile_x
        dy = ty - self.tile_y
        dist = math.sqrt(dx * dx + dy * dy)

        if abs(dx) > abs(dy):
            self.direction = "left" if dx < 0 else "right"
        else:
            self.direction = "back" if dy < 0 else "front"

        step = self.speed / FPS
        self.tile_x += (dx / dist) * step
        self.tile_y += (dy / dist) * step

    def push_away(self, from_x: float, from_y: float, grid: list[list[int]]) -> None:
        ex, ey = self.get_tile_pos()
        dx = ex - int(from_x)
        dy = ey - int(from_y)
        if dx == 0 and dy == 0:
            dx = 1 if random.random() < 0.5 else -1
        else:
            dx = 1 if dx > 0 else -1 if dx < 0 else 0
            dy = 1 if dy > 0 else -1 if dy < 0 else 0
        nx = int(self.tile_x + dx)
        ny = int(self.tile_y + dy)
        if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]) and grid[ny][nx] == TILE_FLOOR:
            self.tile_x, self.tile_y = float(nx), float(ny)
            return
        nx = int(self.tile_x + dx)
        if 0 <= int(self.tile_y) < len(grid) and 0 <= nx < len(grid[0]) and grid[int(self.tile_y)][nx] == TILE_FLOOR:
            self.tile_x = float(nx)
            return
        ny = int(self.tile_y + dy)
        if 0 <= ny < len(grid) and 0 <= int(self.tile_x) < len(grid[0]) and grid[ny][int(self.tile_x)] == TILE_FLOOR:
            self.tile_y = float(ny)


# =============================================================================
#  PYGAME ENGINE (Game Loop & Rendering)
# =============================================================================
class DungeonCrawler:
    """
    Engine chính của game: quản lý vòng lặp game, render, input.

    Tích hợp tất cả các thuật toán:
        - BSP + MST (sinh bản đồ)
        - A* (quái vật tìm đường)
        - BFS + Raycasting (Fog of War)
        - Debug Visualization (F1, F2, F3)
    """
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dungeon Crawler - DSA Visualization")
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_over = False

        # Debug toggles
        self.show_mst = False
        self.show_bsp = False
        self.show_paths = False

        # Map & Entities
        self.dungeon = DungeonMap()
        self.player: Optional[Player] = None
        self.enemies: list[Enemy] = []

        # Player sprites
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sprite_dir = os.path.join(script_dir, "sprites")
        self.player_sprites: dict[str, pygame.Surface] = {}
        for d in ["front", "back", "left", "right"]:
            path = os.path.join(sprite_dir, f"{d}.png")
            try:
                s = pygame.image.load(path).convert_alpha()
                self.player_sprites[d] = pygame.transform.scale(s, (TILE_SIZE, TILE_SIZE))
            except FileNotFoundError:
                pass

        # Enemy sprites (ghost)
        self.enemy_sprites: dict[str, pygame.Surface] = {}
        for d in ["front", "back", "left", "right"]:
            path = os.path.join(sprite_dir, f"ghost_{d}.png")
            try:
                s = pygame.image.load(path).convert_alpha()
                self.enemy_sprites[d] = pygame.transform.scale(s, (TILE_SIZE, TILE_SIZE))
            except FileNotFoundError:
                pass

        # Fog of War
        self.fow = FogOfWar(MAP_ROWS, MAP_COLS)

        # Font
        self.font = pygame.font.SysFont("monospace", 16)
        self.big_font = pygame.font.SysFont("monospace", 48)

        # Fog surface (for alpha blending)
        self.fog_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        # UI
        self.floor = 1

        # Start
        self._init_level()

    def _init_level(self) -> None:
        """
        Khởi tạo một màn chơi mới: sinh bản đồ, spawn player & enemy.
        Time: O(V^2 + E log V) (phụ thuộc vào map generation).
        """
        self.dungeon.generate(bsp_depth=6)

        pos = self.dungeon.find_random_floor()
        self.player = Player(pos[0], pos[1])

        self.enemies.clear()
        for _ in range(random.randint(3, 5)):
            epos = self.dungeon.find_random_floor()
            # Đảm bảo không spawn trùng với player
            if abs(epos[0] - pos[0]) + abs(epos[1] - pos[1]) < 5:
                continue
            self.enemies.append(Enemy(epos[0], epos[1]))

        # Đảm bảo cầu thang không quá gần player
        if self.dungeon.staircase_tile:
            px, py = pos
            sx, sy = self.dungeon.staircase_tile
            if abs(sx - px) + abs(sy - py) < 10:
                farthest_room = max(self.dungeon.rooms, key=lambda r: abs(r.centerx - px) + abs(r.centery - py))
                self.dungeon.staircase_tile = (int(farthest_room.centerx), int(farthest_room.centery))

        self.fow = FogOfWar(MAP_ROWS, MAP_COLS)
        self.game_over = False

    def handle_events(self) -> None:
        """
        Xử lý input từ bàn phím.
        - WASD / Arrow: di chuyển
        - F1: toggle MST edges
        - F2: toggle BSP boundaries
        - F3: toggle enemy paths
        - R: restart
        - ESC: quit
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                if event.key == pygame.K_r and self.game_over:
                    self.floor = 1
                    self._init_level()
                if event.key == pygame.K_F1:
                    self.show_mst = not self.show_mst
                if event.key == pygame.K_F2:
                    self.show_bsp = not self.show_bsp
                if event.key == pygame.K_F3:
                    self.show_paths = not self.show_paths

        # Player movement
        if self.player and self.player.alive:
            keys = pygame.key.get_pressed()
            dx = dy = 0.0

            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx -= 1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx += 1
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                dy -= 1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy += 1
            if dx != 0 or dy != 0:
                self.player.move(dx, dy, self.dungeon.grid)

    def update(self) -> None:
        """
        Cập nhật trạng thái game mỗi frame.
        - Enemy AI (A* pathfinding)
        - Fog of War
        - Collision detection (player vs enemy)
        """
        if self.game_over or not self.player:
            return

        current_time = pygame.time.get_ticks()

        # Update enemies - select up to 3 closest as chasers
        player_tile = self.player.get_tile_pos()
        enemy_dists: list[tuple[float, int]] = []
        for i, enemy in enumerate(self.enemies):
            dx = enemy.tile_x - player_tile[0]
            dy = enemy.tile_y - player_tile[1]
            enemy_dists.append((dx * dx + dy * dy, i))
        enemy_dists.sort()
        chaser_count = min(3, len(self.enemies))
        chaser_indices = {i for _, i in enemy_dists[:chaser_count]}

        for i, enemy in enumerate(self.enemies):
            enemy.update(player_tile, self.dungeon.grid, current_time, i in chaser_indices)

        # Fog of War
        self.fow.compute_visibility(player_tile, self.dungeon.grid, FOV_RADIUS)

        # Staircase -> next floor (check before collision so enemy on stairs doesn't block)
        if self.player.alive and self.dungeon.staircase_tile:
            stair_rect = pygame.Rect(
                self.dungeon.staircase_tile[0] * TILE_SIZE,
                self.dungeon.staircase_tile[1] * TILE_SIZE,
                TILE_SIZE, TILE_SIZE
            )
            if self.player.get_pixel_rect().colliderect(stair_rect):
                self.floor += 1
                self._init_level()
                return

        # Player-Enemy collision (pixel-based)
        player_rect = self.player.get_pixel_rect()
        for enemy in self.enemies:
            enemy_rect = enemy.get_pixel_rect()
            if player_rect.colliderect(enemy_rect):
                self.player.take_damage(1, current_time)
                if not self.player.alive:
                    self.game_over = True
                else:
                    enemy.push_away(self.player.tile_x, self.player.tile_y, self.dungeon.grid)

        # Enemy-Enemy collision - one changes direction
        for i in range(len(self.enemies)):
            for j in range(i + 1, len(self.enemies)):
                e1 = self.enemies[i]
                e2 = self.enemies[j]
                if e1.get_pixel_rect().colliderect(e2.get_pixel_rect()):
                    redirect = e1 if random.random() < 0.5 else e2
                    away = e1 if redirect is e2 else e2
                    dx = redirect.tile_x - away.tile_x
                    dy = redirect.tile_y - away.tile_y
                    if abs(dx) < 0.3 and abs(dy) < 0.3:
                        dx = random.choice([-1, 1])
                        dy = random.choice([-1, 1])
                    dist = math.sqrt(dx * dx + dy * dy)
                    nx = int(redirect.tile_x + (dx / dist) * 4)
                    ny = int(redirect.tile_y + (dy / dist) * 4)
                    nx = max(1, min(MAP_COLS - 2, nx))
                    ny = max(1, min(MAP_ROWS - 2, ny))
                    redirect.redirect_until = current_time + 300
                    if self.dungeon.grid[ny][nx] == TILE_FLOOR:
                        redirect.wander_target = (nx, ny)
                    else:
                        redirect.wander_target = None
                    redirect.path = []
                    redirect.path_index = 0
                    redirect.wander_path_time = 0

    def render(self) -> None:
        """
        Render toàn bộ khung hình.
        Thứ tự: map -> entities -> fog -> debug -> UI.
        """
        self.screen.fill(BLACK)

        # 1. Map tiles
        self._render_map()

        # 2. Staircase
        self._render_staircase()

        # 3. Entities
        self._render_entities()

        # 3. Fog of War
        self._render_fog()

        # 4. Debug overlays
        if self.show_mst:
            self._render_mst_debug()
        if self.show_bsp:
            self._render_bsp_debug()
        if self.show_paths:
            self._render_path_debug()

        # 5. UI
        self._render_ui()

        pygame.display.flip()

    def _render_map(self) -> None:
        """
        Vẽ lưới bản đồ: sàn (floor) và tường (wall).
        Time: O(MAP_ROWS * MAP_COLS).
        """
        for y in range(MAP_ROWS):
            for x in range(MAP_COLS):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if self.dungeon.grid[y][x] == TILE_WALL:
                    pygame.draw.rect(self.screen, WALL_COLOR, rect)
                    pygame.draw.rect(self.screen, (50, 50, 50), rect, 1)
                else:
                    pygame.draw.rect(self.screen, FLOOR_COLOR, rect)
                    pygame.draw.rect(self.screen, (180, 180, 180), rect, 1)

    def _render_entities(self) -> None:
        """
        Vẽ player và enemies.
        Player: hình tròn xanh. Enemy: hình tròn đỏ.
        Time: O(1 + E) với E = số enemy.
        """
        if self.player and self.player.alive:
            rect = self.player.get_pixel_rect()
            sprite = self.player_sprites.get(self.player.direction)
            if sprite:
                self.screen.blit(sprite, rect.topleft)
            else:
                center = rect.center
                pygame.draw.circle(self.screen, PLAYER_COLOR, center, TILE_SIZE // 2 - 2)
                pygame.draw.circle(self.screen, WHITE, center, TILE_SIZE // 2 - 2, 2)

        for enemy in self.enemies:
            enemy_tile = enemy.get_tile_pos()
            if enemy_tile not in self.fow.visible:
                continue
            rect = enemy.get_pixel_rect()
            d = enemy.direction
            if d == "front":
                d = "back"
            sprite = self.enemy_sprites.get(d)
            if sprite:
                self.screen.blit(sprite, rect.topleft)
            else:
                center = rect.center
                pygame.draw.circle(self.screen, ENEMY_COLOR, center, TILE_SIZE // 2 - 2)
                pygame.draw.circle(self.screen, (150, 30, 30), center, TILE_SIZE // 2 - 2, 2)

    def _render_staircase(self) -> None:
        if not self.dungeon.staircase_tile:
            return
        sx, sy = self.dungeon.staircase_tile
        rect = pygame.Rect(sx * TILE_SIZE, sy * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        inner = rect.inflate(-6, -6)
        pygame.draw.rect(self.screen, (180, 130, 40), rect)
        pygame.draw.rect(self.screen, (100, 70, 20), inner)
        pygame.draw.line(self.screen, (220, 180, 80), inner.topleft, inner.bottomright, 3)
        pygame.draw.line(self.screen, (220, 180, 80), inner.topright, inner.bottomleft, 3)

    def _render_fog(self) -> None:
        """
        Vẽ Fog of War: vùng tối ở những ô chưa khám phá,
        vùng mờ ở ô đã khám phá nhưng không trong tầm nhìn.
        Time: O(MAP_ROWS * MAP_COLS).
        """
        self.fog_surface.fill((0, 0, 0, 0))

        for y in range(MAP_ROWS):
            for x in range(MAP_COLS):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if (x, y) not in self.fow.visible:
                    if (x, y) in self.fow.explored:
                        pygame.draw.rect(self.fog_surface, EXPLORED_COLOR, rect)
                    else:
                        pygame.draw.rect(self.fog_surface, HIDDEN_COLOR, rect)

        self.screen.blit(self.fog_surface, (0, 0))

    def _render_mst_debug(self) -> None:
        """
        Vẽ các cạnh của MST (F1) dưới dạng đường thẳng xanh.
        Time: O(E) với E = số cạnh MST.
        """
        for v1, v2, _ in self.dungeon.mst_edges:
            x1 = int(self.dungeon.rooms[v1].centerx * TILE_SIZE)
            y1 = int(self.dungeon.rooms[v1].centery * TILE_SIZE)
            x2 = int(self.dungeon.rooms[v2].centerx * TILE_SIZE)
            y2 = int(self.dungeon.rooms[v2].centery * TILE_SIZE)
            pygame.draw.line(self.screen, DEBUG_MST_COLOR, (x1, y1), (x2, y2), 3)
            # Vẽ chấm tại tâm phòng
            pygame.draw.circle(self.screen, DEBUG_MST_COLOR, (x1, y1), 5)

    def _render_bsp_debug(self) -> None:
        """
        Vẽ ranh giới các node BSP (F2) dạng hình chữ nhật vàng.
        Time: O(n) với n = số node lá BSP.
        """
        if not self.dungeon.bsp_tree:
            return
        for leaf in self.dungeon.bsp_tree.get_leaves():
            rect = pygame.Rect(
                leaf.rect.x * TILE_SIZE, leaf.rect.y * TILE_SIZE,
                leaf.rect.w * TILE_SIZE, leaf.rect.h * TILE_SIZE
            )
            pygame.draw.rect(self.screen, DEBUG_BSP_COLOR, rect, 2)

    def _render_path_debug(self) -> None:
        """
        Vẽ đường đi A* của từng enemy (F3) dạng đường màu hồng.
        Time: O(E * L) với E = số enemy, L = độ dài đường đi.
        """
        for enemy in self.enemies:
            if len(enemy.path) < 2:
                continue
            for i in range(len(enemy.path) - 1):
                x1 = enemy.path[i][0] * TILE_SIZE + TILE_SIZE // 2
                y1 = enemy.path[i][1] * TILE_SIZE + TILE_SIZE // 2
                x2 = enemy.path[i + 1][0] * TILE_SIZE + TILE_SIZE // 2
                y2 = enemy.path[i + 1][1] * TILE_SIZE + TILE_SIZE // 2
                pygame.draw.line(self.screen, DEBUG_PATH_COLOR, (x1, y1), (x2, y2), 2)

    def _render_ui(self) -> None:
        """
        Vẽ giao diện người dùng: máu, tầng, hướng dẫn, debug status.
        Time: O(1).
        """
        if self.game_over:
            text = self.big_font.render("GAME OVER", True, (255, 50, 50))
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(text, text_rect)

            restart_text = self.font.render("Press R to restart | ESC to quit", True, WHITE)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
            self.screen.blit(restart_text, restart_rect)

        # Health bar
        if self.player:
            bar_w = 200
            bar_h = 20
            bar_x = 20
            bar_y = 20
            pygame.draw.rect(self.screen, HEALTH_BG_COLOR, (bar_x, bar_y, bar_w, bar_h))
            health_pct = self.player.health / self.player.max_health
            pygame.draw.rect(
                self.screen, HEALTH_BAR_COLOR,
                (bar_x, bar_y, int(bar_w * health_pct), bar_h)
            )
            pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_w, bar_h), 2)

            # Floor
            floor_text = self.font.render(f"Floor: {self.floor}", True, WHITE)
            self.screen.blit(floor_text, (20, bar_y + bar_h + 10))

            # Instructions
            instr = [
                "WASD/Arrows: Move",
                "F1: MST Edges",
                "F2: BSP Nodes",
                "F3: Enemy Paths",
            ]
            for i, line in enumerate(instr):
                txt = self.font.render(line, True, WHITE if i < 1 else (200, 200, 100))
                self.screen.blit(txt, (20, 70 + i * 22))

            # Debug status
            debug_status = (
                f"MST: {'ON' if self.show_mst else 'OFF'} | "
                f"BSP: {'ON' if self.show_bsp else 'OFF'} | "
                f"Path: {'ON' if self.show_paths else 'OFF'}"
            )
            dst = self.font.render(debug_status, True, (200, 200, 100))
            self.screen.blit(dst, (20, SCREEN_HEIGHT - 30))

    def run(self) -> None:
        """
        Vòng lặp chính của game.
        """
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FPS)

        pygame.quit()


# =============================================================================
#  MAIN ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    game = DungeonCrawler()
    game.run()
