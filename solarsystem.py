import math
import random
import sys
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

# --- Prominently Scaled Solar System Data ---
PLANETS = [
    {"name": "Mercury", "dist": 11.0, "radius": 0.85, "orbit_spd": 2.2, "rot_spd": 2.0,  "tilt": 0.03,  "rings": False, "atmosphere": None},
    {"name": "Venus",   "dist": 16.0, "radius": 1.15, "orbit_spd": 1.6, "rot_spd": -1.5, "tilt": 177.3, "rings": False, "atmosphere": (0.9, 0.8, 0.5, 0.25)},
    {"name": "Earth",   "dist": 22.0, "radius": 1.25, "orbit_spd": 1.2, "rot_spd": 8.0,  "tilt": 23.44, "rings": False, "atmosphere": (0.2, 0.6, 1.0, 0.35)},
    {"name": "Mars",    "dist": 28.0, "radius": 0.95, "orbit_spd": 0.9, "rot_spd": 7.5,  "tilt": 25.19, "rings": False, "atmosphere": (0.8, 0.4, 0.2, 0.20)},
    {"name": "Jupiter", "dist": 38.0, "radius": 2.80, "orbit_spd": 0.5, "rot_spd": 18.0, "tilt": 3.13,  "rings": False, "atmosphere": None},
    {"name": "Saturn",  "dist": 49.0, "radius": 2.30, "orbit_spd": 0.3, "rot_spd": 16.0, "tilt": 26.73, "rings": True,  "atmosphere": None},
    {"name": "Uranus",  "dist": 59.0, "radius": 1.65, "orbit_spd": 0.2, "rot_spd": -10.0,"tilt": 97.77, "rings": False, "atmosphere": (0.4, 0.9, 0.9, 0.25)},
    {"name": "Neptune", "dist": 68.0, "radius": 1.55, "orbit_spd": 0.15,"rot_spd": 12.0, "tilt": 28.32, "rings": False, "atmosphere": (0.2, 0.4, 1.0, 0.30)},
]

def surface_to_texture(surface):
    data = pygame.image.tostring(surface, "RGBA", 1)
    w, h = surface.get_size()
    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGBA, w, h, GL_RGBA, GL_UNSIGNED_BYTE, data)
    return tex_id

def generate_sun_texture():
    surf = pygame.Surface((512, 256))
    surf.fill((255, 130, 0))
    for _ in range(4000):
        x, y = random.randint(0, 512), random.randint(0, 256)
        r = random.randint(2, 9)
        c = random.choice([(255, 230, 110), (255, 80, 0), (255, 255, 220)])
        pygame.draw.circle(surf, c, (x, y), r)
    return surface_to_texture(surf)

def generate_earth_texture():
    surf = pygame.Surface((512, 256))
    surf.fill((12, 55, 140))
    for _ in range(45):
        cx, cy = random.randint(0, 512), random.randint(20, 236)
        rx, ry = random.randint(25, 70), random.randint(18, 50)
        color = (34, 139, 34) if random.random() > 0.35 else (160, 126, 84)
        pygame.draw.ellipse(surf, color, (cx - rx, cy - ry, rx * 2, ry * 2))
    pygame.draw.rect(surf, (240, 245, 255), (0, 0, 512, 24))
    pygame.draw.rect(surf, (240, 245, 255), (0, 232, 512, 24))
    return surface_to_texture(surf)

def generate_jupiter_texture():
    surf = pygame.Surface((512, 256))
    colors = [(195, 155, 115), (145, 95, 65), (225, 205, 175), (115, 65, 45)]
    for y in range(256):
        c = colors[(y // 8) % len(colors)]
        noise = random.randint(-18, 18)
        r, g, b = [max(0, min(255, ch + noise)) for ch in c]
        pygame.draw.line(surf, (r, g, b), (0, y), (512, y))
    pygame.draw.ellipse(surf, (185, 55, 42), (290, 145, 75, 42))
    return surface_to_texture(surf)

def generate_generic_texture(base_rgb, stripe=False):
    surf = pygame.Surface((512, 256))
    surf.fill(base_rgb)
    for y in range(0, 256, 4 if stripe else 10):
        var = random.randint(-22, 22)
        c = tuple(max(0, min(255, ch + var)) for ch in base_rgb)
        pygame.draw.line(surf, c, (0, y), (512, y), 4 if stripe else 10)
    return surface_to_texture(surf)

def generate_glow_billboard_texture():
    surf = pygame.Surface((256, 256), pygame.SRCALPHA)
    for r in range(128, 0, -1):
        alpha = int(255 * (1.0 - (r / 128.0) ** 0.45))
        pygame.draw.circle(surf, (255, 170, 60, alpha), (128, 128), r)
    return surface_to_texture(surf)

def draw_starfield(stars):
    glDisable(GL_LIGHTING)
    glDisable(GL_TEXTURE_2D)
    glBegin(GL_POINTS)
    for x, y, z, color in stars:
        glColor3f(*color)
        glVertex3f(x, y, z)
    glEnd()
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_LIGHTING)

def draw_orbit_path(radius):
    glDisable(GL_LIGHTING)
    glDisable(GL_TEXTURE_2D)
    glDepthMask(GL_FALSE)  # Prevents depth fighting/blinking
    glColor4f(0.4, 0.5, 0.6, 0.25)
    glLineWidth(1.2)
    glBegin(GL_LINE_LOOP)
    for i in range(120):
        theta = 2.0 * math.pi * i / 120
        glVertex3f(radius * math.cos(theta), 0.0, radius * math.sin(theta))
    glEnd()
    glDepthMask(GL_TRUE)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_LIGHTING)

def draw_sun_glow(glow_tex, cam_yaw, cam_pitch):
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glDepthMask(GL_FALSE)  # Prevents Sun glow billboard from occluding planets
    
    glPushMatrix()
    glRotatef(-cam_yaw, 0.0, 1.0, 0.0)
    glRotatef(-cam_pitch, 1.0, 0.0, 0.0)
    
    glBindTexture(GL_TEXTURE_2D, glow_tex)
    glColor4f(1.0, 0.65, 0.25, 0.85)
    
    sz = 11.5
    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex3f(-sz, -sz, 0)
    glTexCoord2f(1, 0); glVertex3f( sz, -sz, 0)
    glTexCoord2f(1, 1); glVertex3f( sz,  sz, 0)
    glTexCoord2f(0, 1); glVertex3f(-sz,  sz, 0)
    glEnd()
    
    glPopMatrix()
    glDepthMask(GL_TRUE)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_LIGHTING)

def draw_atmosphere_halo(quadric, radius, color):
    glDisable(GL_LIGHTING)
    glDisable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glDepthMask(GL_FALSE)  # Prevents atmosphere mesh from z-fighting with planet surface
    glColor4f(*color)
    gluSphere(quadric, radius * 1.05, 36, 36)
    glDepthMask(GL_TRUE)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_LIGHTING)

def main():
    pygame.init()
    
    # Request high precision 24-bit depth buffer & Anti-Aliasing
    pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
    pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)

    display = (900, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Realistic Scaled 3D Solar System (Smooth Render)")

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glEnable(GL_MULTISAMPLE)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # Solar Point Light
    glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 0.0, 0.0, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE,  [1.35, 1.30, 1.20, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [0.9, 0.9, 0.9, 1.0])
    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.03, 0.03, 0.05, 1.0])

    quadric = gluNewQuadric()
    gluQuadricNormals(quadric, GLU_SMOOTH)
    gluQuadricTexture(quadric, GL_TRUE)

    glow_tex = generate_glow_billboard_texture()
    textures = {
        "Sun": generate_sun_texture(),
        "Mercury": generate_generic_texture((140, 130, 125)),
        "Venus":   generate_generic_texture((210, 180, 130), stripe=True),
        "Earth":   generate_earth_texture(),
        "Mars":    generate_generic_texture((190, 80, 45)),
        "Jupiter": generate_jupiter_texture(),
        "Saturn":  generate_generic_texture((210, 190, 140), stripe=True),
        "Uranus":  generate_generic_texture((120, 200, 210)),
        "Neptune": generate_generic_texture((50, 90, 210)),
        "Moon":    generate_generic_texture((160, 160, 160))
    }

    stars = [(random.uniform(-250, 250), random.uniform(-250, 250), random.uniform(-250, 250),
              random.choice([(1.0, 1.0, 1.0), (0.7, 0.8, 1.0), (1.0, 0.9, 0.7)])) for _ in range(1400)]

    cam_dist, cam_pitch, cam_yaw = 85.0, 25.0, 0.0
    mouse_down = False
    last_mouse = (0, 0)
    time_scale, paused = 1.0, False
    show_orbits = True

    for p in PLANETS:
        p["orbit_angle"] = random.uniform(0, 360)
        p["spin_angle"]  = random.uniform(0, 360)

    clock = pygame.time.Clock()

    while True:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                mouse_down = True
                last_mouse = event.pos
            elif event.type == MOUSEBUTTONUP and event.button == 1:
                mouse_down = False
            elif event.type == MOUSEMOTION and mouse_down:
                dx, dy = event.pos[0] - last_mouse[0], event.pos[1] - last_mouse[1]
                cam_yaw += dx * 0.3
                cam_pitch = max(-89.0, min(89.0, cam_pitch + dy * 0.3))
                last_mouse = event.pos
            elif event.type == MOUSEWHEEL:
                cam_dist = max(10.0, min(220.0, cam_dist - event.y * 5.0))
            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    paused = not paused
                elif event.key == K_o:
                    show_orbits = not show_orbits

        if not paused:
            for p in PLANETS:
                p["orbit_angle"] = (p["orbit_angle"] + p["orbit_spd"] * time_scale * 10.0 * dt) % 360
                p["spin_angle"]  = (p["spin_angle"]  + p["rot_spd"]   * time_scale * 18.0 * dt) % 360

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        # Increased near plane to 1.0 to maximize 3D depth buffer precision
        gluPerspective(45.0, (display[0] / display[1]), 1.0, 600.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        rad_yaw, rad_pitch = math.radians(cam_yaw), math.radians(cam_pitch)
        cx = cam_dist * math.sin(rad_yaw) * math.cos(rad_pitch)
        cy = cam_dist * math.sin(rad_pitch)
        cz = cam_dist * math.cos(rad_yaw) * math.cos(rad_pitch)
        gluLookAt(cx, cy, cz, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)

        draw_starfield(stars)

        # Draw Sun Core & Bloom
        glDisable(GL_LIGHTING)
        glBindTexture(GL_TEXTURE_2D, textures["Sun"])
        glColor3f(1.0, 1.0, 1.0)
        gluSphere(quadric, 4.2, 48, 48)
        draw_sun_glow(glow_tex, cam_yaw, cam_pitch)

        # Draw Planets
        for p in PLANETS:
            if show_orbits:
                draw_orbit_path(p["dist"])

            glPushMatrix()
            glRotatef(p["orbit_angle"], 0.0, 1.0, 0.0)
            glTranslatef(p["dist"], 0.0, 0.0)

            # Planet Tilts & Spin
            glRotatef(p["tilt"], 0.0, 0.0, 1.0)
            glRotatef(p["spin_angle"], 0.0, 1.0, 0.0)
            glRotatef(90, 1.0, 0.0, 0.0)

            # Textured Planet Body (Solid Opaque Object)
            glBindTexture(GL_TEXTURE_2D, textures[p["name"]])
            glColor3f(1.0, 1.0, 1.0)
            gluSphere(quadric, p["radius"], 48, 48)

            # Draw optional atmosphere shell with depth mask disabled
            if p["atmosphere"]:
                draw_atmosphere_halo(quadric, p["radius"], p["atmosphere"])

            # Saturn Rings with depth mask disabled
            if p["rings"]:
                glDisable(GL_LIGHTING)
                glDisable(GL_TEXTURE_2D)
                glDepthMask(GL_FALSE)
                glColor4f(0.85, 0.75, 0.55, 0.75)
                glBegin(GL_QUAD_STRIP)
                for i in range(73):
                    theta = 2.0 * math.pi * i / 72
                    c, s = math.cos(theta), math.sin(theta)
                    glVertex3f(p["radius"] * 1.35 * c, p["radius"] * 1.35 * s, 0)
                    glVertex3f(p["radius"] * 2.40 * c, p["radius"] * 2.40 * s, 0)
                glEnd()
                glDepthMask(GL_TRUE)
                glEnable(GL_TEXTURE_2D)
                glEnable(GL_LIGHTING)

            # Earth Moon
            if p["name"] == "Earth":
                glPushMatrix()
                glRotatef(p["orbit_angle"] * 3.5, 0.0, 0.0, 1.0)
                glTranslatef(2.1, 0.0, 0.0)
                glBindTexture(GL_TEXTURE_2D, textures["Moon"])
                gluSphere(quadric, 0.32, 24, 24)
                glPopMatrix()

            glPopMatrix()

        pygame.display.flip()

if __name__ == "__main__":
    main()