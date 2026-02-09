from manim import *
import json
import numpy as np

def intensity_to_color(intensity):
    """
    将 intensity (0-255) 映射为恒星颜色：
    - 暗星（低亮度） → 红/橙（低温）
    - 中等亮度 → 黄/白
    - 亮星（高亮度） → 白/蓝（高温）
    """
    t = min(1.0, max(0.0, intensity / 255.0))
    if t < 0.3:
        return interpolate_color(RED, ORANGE, t / 0.3)
    elif t < 0.6:
        return interpolate_color(ORANGE, YELLOW, (t - 0.3) / 0.3)
    elif t < 0.85:
        return interpolate_color(YELLOW, WHITE, (t - 0.6) / 0.25)
    else:
        return interpolate_color(WHITE, BLUE, (t - 0.85) / 0.15)

class StarFieldAnimation(Scene):
    def construct(self):
        # === 加载星星数据 ===
        json_path = 'star_positions.json'
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            stars = data['stars']
            print(f"原始星星数量: {len(stars)}")

            if len(stars) > 5000:
                stars = list(np.random.choice(len(stars), 5000, replace=False))
                stars = [data['stars'][i] for i in stars]
            
            print(f"随机选择了 {len(stars)} 颗星星用于渲染")
        except FileNotFoundError:
            print("未找到 star_positions.json，使用随机星星")
            stars = []
            for _ in range(200):
                angle = np.random.uniform(0, 2 * PI)
                r = np.random.uniform(0.5, 4.0)
                intensity = np.random.randint(150, 255)
                stars.append({
                    'x': r * np.cos(angle),
                    'y': r * np.sin(angle),
                    'intensity': intensity
                })

        self.camera.background_color = BLACK

        # === 坐标归一化 ===
        if stars:
            xs = [s['x'] for s in stars]
            ys = [s['y'] for s in stars]
            max_x = max(abs(x) for x in xs) or 1
            max_y = max(abs(y) for y in ys) or 1
            scale_x = 4.0 / max_x
            scale_y = 2.0 / max_y
        else:
            scale_x = scale_y = 1

        # === 创建星星对象（不立即添加到场景）===
        star_objects = VGroup()
        target_opacities = []  # 存储每个星星的目标透明度

        for star in stars:
            x = star['x'] * scale_x
            y = star['y'] * scale_y
            intensity_val = star['intensity']
            intensity_norm = intensity_val / 255.0
            radius = 0.01 + intensity_norm * 0.02     
            brightness = 0.4 + intensity_norm * 0.6    # 基础亮度足够

            target_opacities.append(brightness)
            star_color = intensity_to_color(intensity_val)  # ← 动态颜色！

            # 主星：实心圆
            main_star = Circle(
                radius=radius,
                fill_color=star_color,
                fill_opacity=1.0,
                stroke_width=0
            ).move_to([x, y, 0])
            main_star.set_opacity(0)  # 初始隐藏

            # 辉光（仅亮星）
            if brightness > 0.8:
                glow = Circle(
                    radius=radius * 2.5,
                    fill_color=star_color,
                    fill_opacity=1.0,
                    stroke_width=0
                ).move_to([x, y, 0])
                glow.set_opacity(0)
                star_obj = VGroup(main_star, glow)
            else:
                star_obj = main_star

            star_objects.add(star_obj)

        # ========================================
        # ✅ 动画序列（严格按顺序）
        # ========================================

        # 1. 标题入场
        main_title = Text("ESO1242a", font_size=64, color=YELLOW)
        main_title.to_edge(UP)
        subtitle = Text("Star Field Visualization", font_size=36, color=BLUE_C)
        subtitle.next_to(main_title, DOWN, buff=0.3)

        self.play(Write(main_title), Write(subtitle), run_time=2)
        self.wait(1)

        # 2. 标题上移
        title_group = VGroup(main_title, subtitle)
        self.play(title_group.animate.to_edge(UP, buff=0.2).scale(0.9), run_time=1)

        # 3. ✅ 此时才将星星加入场景并渐入（关键！）
        self.add(star_objects)  # 在标题之后添加！

        # 按距离排序（从中心向外）
        distances = [
            np.hypot(star['x'] * scale_x, star['y'] * scale_y)
            for star in stars
        ]
        sorted_indices = np.argsort(distances)

        # 分组渐入
        num_groups = 6
        group_size = len(stars) // num_groups
        for i in range(num_groups):
            start = i * group_size
            end = (i + 1) * group_size if i < num_groups - 1 else len(stars)
            anims = [
                star_objects[idx].animate.set_opacity(target_opacities[idx])
                for idx in sorted_indices[start:end]
            ]
            self.play(AnimationGroup(*anims, lag_ratio=0.01), run_time=0.8)
        self.wait(0.5)

        # 4. 旋转星空
        self.play(Rotate(star_objects, angle=PI/4, about_point=ORIGIN, run_time=2))
        self.wait(0.5)

        # 5. 星座连线
        if stars:
            bright_stars = sorted(stars, key=lambda s: s['intensity'], reverse=True)[:8]
            lines = VGroup()
            for i in range(len(bright_stars) - 1):
                p1 = [bright_stars[i]['x'] * scale_x, bright_stars[i]['y'] * scale_y, 0]
                p2 = [bright_stars[i+1]['x'] * scale_x, bright_stars[i+1]['y'] * scale_y, 0]
                line = Line(p1, p2, color=BLUE_C, stroke_width=1.8, stroke_opacity=0.7)
                line.set_opacity(0)
                lines.add(line)
                self.add(line)

            if lines:
                self.play(
                    LaggedStart(*[line.animate.set_opacity(0.7) for line in lines], lag_ratio=0.2),
                    run_time=2
                )
                self.wait(1.5)
                self.play(FadeOut(lines, run_time=1))

        # 6. 数据统计面板
        if stars:
            panel = Rectangle(width=5, height=4, color=BLUE_E, fill_color=BLACK, fill_opacity=0.85, stroke_width=2)
            panel.to_corner(DL, buff=0.5)
            panel_title = Text("统计数据", font_size=28, color=YELLOW)
            panel_title.next_to(panel.get_top(), DOWN, buff=0.2)

            stats = VGroup(
                Text(f"星星总数: {len(stars)}", font_size=22),
                Text(f"最大亮度: {max(s['intensity'] for s in stars):.0f}", font_size=22),
                Text(f"平均亮度: {np.mean([s['intensity'] for s in stars]):.0f}", font_size=22),
                Text(f"X 范围: [{min(s['x'] for s in stars):.1f}, {max(s['x'] for s in stars):.1f}]", font_size=22),
                Text(f"Y 范围: [{min(s['y'] for s in stars):.1f}, {max(s['y'] for s in stars):.1f}]", font_size=22)
            )
            stats.arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to(panel.get_center())
            stats.set_color(WHITE)

            self.play(FadeIn(panel), Write(panel_title), run_time=1)
            self.play(LaggedStart(*[Write(t) for t in stats], lag_ratio=0.15), run_time=2)
            self.wait(3)
            self.play(FadeOut(panel, panel_title, stats), run_time=1)

        # 7. 闪烁效果
        if stars:
            bright_indices = [i for i, s in enumerate(stars) if s['intensity'] > 200][:12]
            flash_anims = []
            for i in bright_indices:
                obj = star_objects[i]
                orig = target_opacities[i]
                flash = Succession(
                    obj.animate.set_opacity(min(orig * 2.2, 1.0)),
                    obj.animate.set_opacity(orig),
                    obj.animate.set_opacity(min(orig * 2.2, 1.0)),
                    obj.animate.set_opacity(orig),
                    lag_ratio=0.25
                )
                flash_anims.append(flash)
            if flash_anims:
                self.play(AnimationGroup(*flash_anims, lag_ratio=0.08), run_time=3)
        self.wait(1)

        # 8. 最终展示
        final_title = Text("ESO1242a", font_size=48, color=YELLOW)
        final_subtitle = Text("Stellar Cluster", font_size=28, color=BLUE_C)
        final_subtitle.next_to(final_title, DOWN, buff=0.2)
        final_group = VGroup(final_title, final_subtitle).to_edge(UP)
        self.play(Transform(title_group, final_group), run_time=1.2)
        self.play(Rotate(star_objects, angle=PI/2, about_point=ORIGIN, run_time=3))
        self.wait(1)

        # 9. 结尾字幕
        self.play(
            FadeOut(final_group, shift=UP),
            FadeOut(star_objects, shift=DOWN),
            run_time=1.5
        )

        ending = VGroup(
            Text("感谢观看", font_size=56, color=YELLOW),
            Text("Exploring the Cosmos, One Star at a Time", font_size=32, color=BLUE_C)
        )
        ending.arrange(DOWN, buff=0.4).move_to(ORIGIN)
        self.play(FadeIn(ending[0]), run_time=1.2)
        self.wait(0.5)
        self.play(FadeIn(ending[1]), run_time=1.0)
        self.wait(3)
        self.play(FadeOut(ending), run_time=2)

# === 运行配置 ===
if __name__ == "__main__":
    config.frame_size = (1920, 1080)
    config.pixel_width = 1920
    config.pixel_height = 1080
    config.frame_rate = 30
    config.background_color = BLACK
    config.output_file = "ESO1242a_star_field.mp4"

    scene = StarFieldAnimation()
    scene.render()
    print("✅ 动画已生成: ESO1242a_star_field.mp4")
