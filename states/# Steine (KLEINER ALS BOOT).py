        # Steine (KLEINER ALS BOOT)
        self.rock_img = pg.image.load("assets/Stein.png").convert_alpha()
        self.rock_img = pg.transform.scale_by(self.rock_img, 0.5)  # <<< kleiner
        self.rock_mask = pg.mask.from_surface(self.rock_img)

        self.rocks = []
        self.rock_rects = []

        max_rocks = 120
        tries_per_rock = 200

        for _ in range(max_rocks):
            for _ in range(tries_per_rock):
                pos = pg.Vector2(
                    random.randint(0, int(self.world_size.x)),
                    random.randint(0, int(self.world_size.y)),
                )
                rect = self.rock_img.get_rect(topleft=pos)

                if rect.colliderect(self.insel_rect):
                    continue

                if any(rect.colliderect(r) for r in self.rock_rects):
                    continue

                self.rocks.append(pos)
                self.rock_rects.append(rect)
                break








                    # Stein-Kollision
        for rock_rect in self.rock_rects:
            offset = (
                int(rock_rect.left - self.ship_rect.left),
                int(rock_rect.top - self.ship_rect.top),
            )
            if ship_mask.overlap(self.rock_mask, offset):
                self.ship_pos = old_pos
                break
















            # Kamera + Zoom
        self.camera_pos += (self.ship_pos - self.camera_pos) * min(1, dt * self.cam_lerp)
        target_zoom = self.move_zoom if self.moving else self.base_zoom
        self.zoom += (target_zoom - self.zoom) * min(1, dt * self.zoom_speed)

    def draw(self, s):
        w, h = s.get_size()
        surf = pg.Surface((w, h), pg.SRCALPHA)

        tile = int(time() * 2)
        start_x = int((self.camera_pos.x - w // 2) // 64) - 1
        start_y = int((self.camera_pos.y - h // 2) // 64) - 1

        for i in range(start_x, start_x + w // 64 + 3):
            for j in range(start_y, start_y + h // 64 + 3):
                world_pos = pg.Vector2(i * 64, j * 64)
                screen_pos = world_pos - self.camera_pos + pg.Vector2(w // 2, h // 2)
                surf.blit(self.tiles[(tile + i) % 4], screen_pos)

        surf.blit(
            self.insel,
            self.insel_pos - self.camera_pos + pg.Vector2(w // 2, h // 2),
        )

        for rock_pos in self.rocks:
            surf.blit(
                self.rock_img,
                rock_pos - self.camera_pos + pg.Vector2(w // 2, h // 2),
            )

        ship_draw_pos = self.ship_rect.topleft - self.camera_pos + pg.Vector2(w // 2, h // 2)
        surf.blit(self.ship, ship_draw_pos)

        scaled = pg.transform.smoothscale(
            surf,
            (int(w * self.zoom), int(h * self.zoom)),
        )
        s.blit(scaled, scaled.get_rect(center=(w // 2, h // 2)))



 # Welt
        self.world_size = pg.Vector2(4000, 4000)
