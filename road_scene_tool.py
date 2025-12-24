import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from dataclasses import dataclass
from typing import Dict, Optional
from PIL import ImageGrab


CANVAS_WIDTH = 1100
CANVAS_HEIGHT = 520
ROAD_MARGIN = 60
LANE_COUNT = 3
LANE_COLOR = "#303030"
LANE_MARK_COLOR = "#e6e6e6"
SHOULDER_COLOR = "#1f1f1f"
BACKGROUND_COLOR = "#ffffff"


@dataclass
class Vehicle:
    vehicle_id: int
    role: str
    x: float
    y: float


class RoadSceneApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("车辆行驶场景绘制 MVP")
        self.vehicles: Dict[int, Vehicle] = {}
        self.active_vehicle_id: Optional[int] = None
        self.drag_offset = (0.0, 0.0)
        self.vehicle_counter = 1

        self._build_ui()
        self._bind_events()
        self._init_scene()

    def _build_ui(self) -> None:
        self.root.configure(bg="#f6f6f6")
        control_frame = ttk.Frame(self.root, padding=(12, 10))
        control_frame.pack(fill=tk.X)

        ttk.Label(control_frame, text="道路结构：").pack(side=tk.LEFT)
        self.scene_var = tk.StringVar(value="高速三车道直路")
        self.scene_menu = ttk.Combobox(
            control_frame,
            textvariable=self.scene_var,
            values=["高速三车道直路", "高速匝道汇入主路", "高速汇出匝道"],
            state="readonly",
            width=20,
        )
        self.scene_menu.pack(side=tk.LEFT, padx=(0, 12))
        self.scene_menu.bind("<<ComboboxSelected>>", lambda _: self._render_scene())

        ttk.Button(control_frame, text="添加 NPC 车辆", command=self.add_npc).pack(side=tk.LEFT, padx=4)
        ttk.Button(control_frame, text="删除选中车辆", command=self.remove_selected).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(control_frame, text="下载 JPG", command=self.save_jpg).pack(side=tk.LEFT, padx=4)

        hint_frame = ttk.Frame(self.root, padding=(12, 0))
        hint_frame.pack(fill=tk.X)
        ttk.Label(
            hint_frame,
            text="提示：点击车辆可选中，按住拖动可移动位置。自车为蓝色，NPC 为灰色。",
            foreground="#555",
        ).pack(anchor="w")

        self.canvas = tk.Canvas(
            self.root,
            width=CANVAS_WIDTH,
            height=CANVAS_HEIGHT,
            bg=BACKGROUND_COLOR,
            highlightthickness=1,
            highlightbackground="#cfcfcf",
        )
        self.canvas.pack(padx=12, pady=12)

    def _bind_events(self) -> None:
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

    def _init_scene(self) -> None:
        self.vehicles.clear()
        self.vehicle_counter = 1
        self.add_vehicle(role="ego", x=350, y=CANVAS_HEIGHT / 2)
        self._render_scene()

    def _render_scene(self) -> None:
        self.canvas.delete("all")
        self._draw_road()
        for vehicle in self.vehicles.values():
            self._draw_vehicle(vehicle)

    def _draw_road(self) -> None:
        scene = self.scene_var.get()
        if scene == "高速三车道直路":
            self._draw_straight_road()
        elif scene == "高速匝道汇入主路":
            self._draw_merge_road()
        else:
            self._draw_exit_road()

    def _draw_straight_road(self) -> None:
        top = ROAD_MARGIN
        bottom = CANVAS_HEIGHT - ROAD_MARGIN
        self.canvas.create_rectangle(40, top, CANVAS_WIDTH - 40, bottom, fill="#f5f5f5", outline="")
        self.canvas.create_rectangle(40, top, CANVAS_WIDTH - 40, top + 18, fill=SHOULDER_COLOR, outline="")
        self.canvas.create_rectangle(
            40, bottom - 18, CANVAS_WIDTH - 40, bottom, fill=SHOULDER_COLOR, outline=""
        )
        lane_height = (bottom - top) / LANE_COUNT
        for i in range(1, LANE_COUNT):
            y = top + i * lane_height
            self.canvas.create_line(
                60,
                y,
                CANVAS_WIDTH - 60,
                y,
                fill=LANE_MARK_COLOR,
                width=3,
                dash=(18, 14),
            )
        self.canvas.create_line(40, top, CANVAS_WIDTH - 40, top, fill=LANE_COLOR, width=3)
        self.canvas.create_line(40, bottom, CANVAS_WIDTH - 40, bottom, fill=LANE_COLOR, width=3)

    def _draw_merge_road(self) -> None:
        self._draw_straight_road()
        merge_start_x = CANVAS_WIDTH - 560
        merge_end_x = CANVAS_WIDTH - 40
        outer_edge = [
            (merge_start_x, ROAD_MARGIN - 45),
            (merge_start_x + 140, ROAD_MARGIN - 80),
            (merge_start_x + 300, ROAD_MARGIN - 55),
            (merge_end_x, ROAD_MARGIN - 25),
        ]
        inner_edge = [
            (merge_start_x, ROAD_MARGIN + 30),
            (merge_start_x + 140, ROAD_MARGIN + 10),
            (merge_start_x + 300, ROAD_MARGIN),
            (merge_end_x, ROAD_MARGIN + 12),
        ]
        ramp_polygon = self._flatten_points(outer_edge + list(reversed(inner_edge)))
        self.canvas.create_polygon(
            *ramp_polygon,
            fill="#f5f5f5",
            outline=LANE_COLOR,
            width=3,
            smooth=True,
        )
        self.canvas.create_line(
            *self._flatten_points(inner_edge),
            fill=LANE_MARK_COLOR,
            width=2,
            dash=(14, 10),
            smooth=True,
        )

    def _draw_exit_road(self) -> None:
        self._draw_straight_road()
        split_x = CANVAS_WIDTH - 520
        exit_end_x = CANVAS_WIDTH - 40
        outer_edge = [
            (split_x, ROAD_MARGIN - 10),
            (split_x + 160, ROAD_MARGIN - 55),
            (split_x + 320, ROAD_MARGIN - 95),
            (exit_end_x, ROAD_MARGIN - 115),
        ]
        inner_edge = [
            (split_x, ROAD_MARGIN + 40),
            (split_x + 160, ROAD_MARGIN + 8),
            (split_x + 320, ROAD_MARGIN - 20),
            (exit_end_x, ROAD_MARGIN - 35),
        ]
        ramp_polygon = self._flatten_points(outer_edge + list(reversed(inner_edge)))
        self.canvas.create_polygon(
            *ramp_polygon,
            fill="#f5f5f5",
            outline=LANE_COLOR,
            width=3,
            smooth=True,
        )
        self.canvas.create_line(
            *self._flatten_points(inner_edge),
            fill=LANE_MARK_COLOR,
            width=2,
            dash=(14, 10),
            smooth=True,
        )
        self.canvas.create_line(
            split_x,
            ROAD_MARGIN + 40,
            split_x + 60,
            ROAD_MARGIN + 8,
            fill=LANE_COLOR,
            width=3,
        )

    @staticmethod
    def _flatten_points(points: list[tuple[float, float]]) -> list[float]:
        return [coord for point in points for coord in point]

    def _draw_vehicle(self, vehicle: Vehicle) -> None:
        width = 70
        height = 36
        x0 = vehicle.x - width / 2
        y0 = vehicle.y - height / 2
        x1 = vehicle.x + width / 2
        y1 = vehicle.y + height / 2
        fill = "#2b6cb0" if vehicle.role == "ego" else "#5f5f5f"
        outline = "#1e3c68" if vehicle.role == "ego" else "#3d3d3d"
        tag = f"vehicle_{vehicle.vehicle_id}"
        rect = self.canvas.create_rectangle(
            x0,
            y0,
            x1,
            y1,
            fill=fill,
            outline=outline,
            width=2,
            tags=("vehicle", tag),
        )
        label = "自车" if vehicle.role == "ego" else f"NPC {vehicle.vehicle_id}"
        self.canvas.create_text(
            vehicle.x,
            vehicle.y,
            text=label,
            fill="#ffffff",
            font=("Arial", 10, "bold"),
            tags=("vehicle", tag),
        )
        if vehicle.vehicle_id == self.active_vehicle_id:
            self.canvas.create_rectangle(
                x0 - 4,
                y0 - 4,
                x1 + 4,
                y1 + 4,
                outline="#f59e0b",
                width=2,
                dash=(6, 4),
            )
        return rect

    def add_vehicle(self, role: str, x: float, y: float) -> None:
        vehicle = Vehicle(vehicle_id=self.vehicle_counter, role=role, x=x, y=y)
        self.vehicles[self.vehicle_counter] = vehicle
        self.vehicle_counter += 1

    def add_npc(self) -> None:
        x = CANVAS_WIDTH / 2 + 100
        y = CANVAS_HEIGHT / 2 + (self.vehicle_counter % 3 - 1) * 50
        self.add_vehicle("npc", x=x, y=y)
        self._render_scene()

    def remove_selected(self) -> None:
        if self.active_vehicle_id is None:
            messagebox.showinfo("提示", "请先选中要删除的车辆。")
            return
        if self.vehicles[self.active_vehicle_id].role == "ego":
            messagebox.showwarning("提示", "自车不可删除。")
            return
        del self.vehicles[self.active_vehicle_id]
        self.active_vehicle_id = None
        self._render_scene()

    def on_mouse_down(self, event: tk.Event) -> None:
        self.active_vehicle_id = None
        for item in self.canvas.find_withtag("current"):
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag.startswith("vehicle_"):
                    vehicle_id = int(tag.split("_")[-1])
                    self.active_vehicle_id = vehicle_id
                    vehicle = self.vehicles[vehicle_id]
                    self.drag_offset = (vehicle.x - event.x, vehicle.y - event.y)
                    break
        self._render_scene()

    def on_mouse_drag(self, event: tk.Event) -> None:
        if self.active_vehicle_id is None:
            return
        vehicle = self.vehicles[self.active_vehicle_id]
        vehicle.x = max(70, min(CANVAS_WIDTH - 70, event.x + self.drag_offset[0]))
        vehicle.y = max(ROAD_MARGIN + 20, min(CANVAS_HEIGHT - ROAD_MARGIN - 20, event.y + self.drag_offset[1]))
        self._render_scene()

    def on_mouse_up(self, event: tk.Event) -> None:
        if self.active_vehicle_id is None:
            return
        self._render_scene()

    def save_jpg(self) -> None:
        self.root.update()
        x = self.canvas.winfo_rootx()
        y = self.canvas.winfo_rooty()
        x1 = x + self.canvas.winfo_width()
        y1 = y + self.canvas.winfo_height()
        try:
            image = ImageGrab.grab(bbox=(x, y, x1, y1))
        except Exception as exc:  # noqa: BLE001 - display error message to user
            messagebox.showerror("导出失败", f"截图失败，请确认系统允许截图：{exc}")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".jpg",
            filetypes=[("JPEG 图片", "*.jpg"), ("PNG 图片", "*.png")],
        )
        if not file_path:
            return
        image.save(file_path, quality=95)
        messagebox.showinfo("保存成功", f"已保存到: {file_path}")


if __name__ == "__main__":
    app_root = tk.Tk()
    style = ttk.Style(app_root)
    style.configure("TButton", padding=6)
    style.configure("TCombobox", padding=4)
    RoadSceneApp(app_root)
    app_root.mainloop()
