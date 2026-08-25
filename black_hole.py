import math
import random
import sys
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

def generate_deep_space_starfield(count=1600, radius=300.0):
    """Generates background starlight with realistic spectral temperature distribution."""
    stars = []
    colors = [
        (1.0, 1.0, 1.0),   # White
        (0.65, 0.8, 1.0),  # Blue giant
        (1.0, 0.85, 0.6),  # Yellow/Orange
        (1.0, 0.5, 0.4)    # Red dwarf
    ]
    for _ in range(count):
        theta = random.uniform(0, 2 * math.pi)
        phi = random.uniform(-math.pi / 2, math.pi / 2)
        r = random.uniform(radius * 0.85, radius * 1.15)
        x = r * math.cos(phi) * math.sin(theta)
        y = r * math.sin(phi)
        z = r * math.cos(phi) * math.cos(theta)
        color = random.choice(colors)
        size = random.choice([1.0, 1.5, 2.0, 2.5])
        stars.append((x, y, z, color, size))
    return stars

def draw_starfield(stars):
    """Renders background starlight."""
    glDisable(GL_LIGHTING)
    glDisable(GL_TEXTURE_2D)
    glDepthMask(GL_FALSE)
    for x, y, z, color, size in stars:
        glPointSize(size)
        glBegin(GL_POINTS)
        glColor3f(*color)
        glVertex3f(x, y, z)
        glEnd()
    glDepthMask(GL_TRUE)

def draw_event_horizon(quadric, radius=3.0):
    """Renders the central Event Horizon (absolute light-capturing void)."""
    glEnable(GL_LIGHTING)
    glDepthMask(GL_TRUE)
    
    # Absolute zero reflectivity black hole core
    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, [0.0, 0.0, 0.0, 1.0])
    glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, [0.0, 0.0, 0.0, 1.0])
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.0, 0.0, 0.0, 1.0])
    glColor3f(0.0, 0.0, 0.0)
    
    gluSphere(quadric, radius, 64, 64)

def draw_photon_sphere(quadric, radius=3.4, t=0.0):
    """Renders the glowing Photon Sphere (thin ring where photons orbit in unstable equilibrium)."""
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glDepthMask(GL_FALSE)

    # Multi-layered glowing halo shell around event horizon
    glow_layers = [
        (radius * 1.01, (1.0, 0.95, 0.7, 0.85)),
        (radius * 1.08, (1.0, 0.60, 0.2, 0.45)),
        (radius * 1.18, (0.8, 0.30, 0.1, 0.20))
    ]
    for r, col in glow_layers:
        glColor4f(*col)
        gluSphere(quadric, r, 48, 48)

    glDepthMask(GL_TRUE)

def draw_accretion_disk(t, r_in=3.8, r_out=16.0, rings=45, segments=120):
    """
    Renders the relativistic plasma accretion disk with Keplerian differential rotation
    and Doppler beaming (approaching side blue-shifted & brighter, receding side red-shifted).
    """
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)  # Additive intense plasma glow
    glDepthMask(GL_FALSE)

    dr = (r_out - r_in) / rings

    for i in range(rings):
        r1 = r_in + i * dr
        r2 = r1 + dr

        # Keplerian orbital velocity profile: inner gas rotates significantly faster
        speed1 = (r_in / r1) ** 1.5 * 1.8
        speed2 = (r_in / r2) ** 1.5 * 1.8

        # Normalized radial temperature gradient (Inner: white-cyan hot -> Outer: deep red)
        norm_r = (r1 - r_in) / (r_out - r_in)

        glBegin(GL_QUAD_STRIP)
        for j in range(segments + 1):
            angle = (2.0 * math.pi * j / segments)
            
            # Rotate vertices based on orbital velocity over time
            a1 = angle + t * speed1
            a2 = angle + t * speed2

            # Doppler Beaming Factor (Moving towards viewer = brighter & blue-shifted)
            doppler_factor = math.cos(angle)  
            beaming = max(0.2, 1.0 + 0.65 * doppler_factor)

            # Relativistic color mapping
            if norm_r < 0.15:
                # Superheated Inner Core (White/Blue Plasma)
                base_color = (0.7 + 0.3 * beaming, 0.85 * beaming, 1.0 * beaming)
            elif norm_r < 0.55:
                # Mid Disk (Gold / Intense Orange)
                base_color = (1.0 * beaming, (0.6 - norm_r * 0.4) * beaming, 0.1 * beaming)
            else:
                # Outer Boundary (Deep Red Dust)
                base_color = ((0.8 - norm_r * 0.5) * beaming, 0.08 * beaming, 0.02 * beaming)

            alpha = (1.0 - (norm_r ** 1.4)) * 0.75 * beaming
            glColor4f(base_color[0], base_color[1], base_color[2], max(0.0, min(1.0, alpha)))

            # Disk geometry coordinates
            x1, z1 = r1 * math.cos(a1), r1 * math.sin(a1)
            x2, z2 = r2 * math.cos(a2), r2 * math.sin(a2)
            
            # Subtle vertical turbulence oscillation
            y1 = math.sin(a1 * 6.0 + t * 3.0) * 0.08 * (1.0 + norm_r)
            y2 = math.sin(a2 * 6.0 + t * 3.0) * 0.08 * (1.0 + norm_r)

            glVertex3f(x1, y1, z1)
            glVertex3f(x2, y2, z2)
        glEnd()

    glDepthMask(GL_TRUE)

def draw_gravitational_lensing_arcs(t, r_in=3.8, r_out=15.0, segments=90):
    """
    Renders simulated General Relativity gravitational lensing: 
    Bends light from the rear of the accretion disk over the top and bottom of the event horizon.
    """
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glDepthMask(GL_FALSE)

    for orientation in [1.0, -1.0]:  # Top arch and bottom arch lensing
        glBegin(GL_QUAD_STRIP)
        for j in range(segments + 1):
            # Lensing arc spans across the rear hemisphere of the black hole
            angle = math.pi * (0.05 + 0.90 * j / segments)
            
            # Curvature calculation wrapping around event horizon
            c, s = math.cos(angle), math.sin(angle)
            
            # Warp geometry over the event horizon sphere
            lens_radius = 3.3 + 1.2 * math.sin(angle)
            x = lens_radius * c * 1.8
            y = orientation * (3.1 + 2.5 * math.sin(angle))
            z = -lens_radius * s * 0.5

            # Distance fallback thickness
            thickness = 0.95 * math.sin(angle)
            
            # Color profile matching lensed light
            doppler = max(0.2, 1.0 + 0.5 * c)
            r_col = min(1.0, 1.0 * doppler)
            g_col = min(1.0, 0.65 * doppler)
            b_col = min(1.0, 0.25 * doppler)
            alpha = 0.60 * math.sin(angle)

            glColor4f(r_col, g_col, b_col, alpha)
            glVertex3f(x, y, z)
            glColor4f(r_col * 0.5, g_col * 0.3, b_col * 0.1, 0.0)
            glVertex3f(x, y + orientation * thickness, z)
        glEnd()

    glDepthMask(GL_TRUE)

def draw_relativistic_jets(t, length=24.0, radius=2.8):
    """Renders twin high-energy plasma jets blasting from the rotational poles."""
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glDepthMask(GL_FALSE)

    for direction in [1.0, -1.0]:  # North and South polar jets
        glBegin(GL_QUAD_STRIP)
        segments = 36
        for i in range(segments + 1):
            u = i / float(segments)
            y = direction * (3.0 + u * length)
            
            # Narrow collimated cone profile
            r = (0.2 + (u ** 1.8) * radius) * (1.0 + 0.05 * math.sin(u * 20.0 - t * 8.0))
            angle = (u * math.pi * 4.0 + t * 4.0)
            x = r * math.cos(angle)
            z = r * math.sin(angle)

            alpha = (1.0 - u) * 0.55
            # Violet-Cyan high-energy gamma spectral glow
            glColor4f(0.5 + 0.5 * u, 0.75, 1.0, alpha)
            glVertex3f(x, y, z)
            glColor4f(0.2, 0.4, 0.9, 0.0)
            glVertex3f(x * 1.8, y, z * 1.8)
        glEnd()

    glDepthMask(GL_TRUE)

def generate_accretion_infall_particles(count=300):
    """Spawns gas particles spiraling inward toward the event horizon."""
    particles = []
    for _ in range(count):
        r = random.uniform(3.8, 18.0)
        theta = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0.5, 1.5)
        particles.append([r, theta, speed])
    return particles

def update_and_draw_infall_particles(particles, dt, t):
    """Renders active particle streams falling across the accretion plane."""
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glDepthMask(GL_FALSE)
    
    glPointSize(2.5)
    glBegin(GL_POINTS)
    for p in particles:
        # Spiral inward movement logic
        p[0] -= p[2] * 0.8 * dt  # Decrease radius
        p[1] += (4.0 / max(1.0, p[0])) * dt  # Faster spin near origin
        
        # Reset particle if consumed by event horizon
        if p[0] <= 3.1:
            p[0] = random.uniform(14.0, 18.0)
            p[1] = random.uniform(0, 2 * math.pi)

        x = p[0] * math.cos(p[1])
        z = p[0] * math.sin(p[1])
        y = math.sin(p[1] * 4.0 + t) * 0.1

        alpha = min(1.0, (p[0] - 3.0) / 4.0)
        glColor4f(1.0, 0.85, 0.4, alpha * 0.8)
        glVertex3f(x, y, z)
    glEnd()
    glDepthMask(GL_TRUE)

def main():
    pygame.init()

    # Configure High-Precision 24-bit Depth Buffer & Anti-Aliasing Context
    pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
    pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)

    display = (900, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Kerr Black Hole with Gravitational Lensing Simulation")

    # OpenGL Settings
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glEnable(GL_MULTISAMPLE)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # Ambient Light Setup
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, [0.0, 0.0, 0.0, 1.0])
    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.02, 0.02, 0.03, 1.0])

    quadric = gluNewQuadric()
    gluQuadricNormals(quadric, GLU_SMOOTH)

    stars = generate_deep_space_starfield()
    particles = generate_accretion_infall_particles()

    # Camera Orbiting Controls
    cam_dist, cam_pitch, cam_yaw = 28.0, 14.0, 25.0
    mouse_down = False
    last_mouse = (0, 0)
    
    time_scale = 1.0
    paused = False
    total_time = 0.0

    clock = pygame.time.Clock()

    while True:
        dt = clock.tick(60) / 1000.0
        if not paused:
            total_time += dt * time_scale

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
                cam_dist = max(5.0, min(120.0, cam_dist - event.y * 2.5))
            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    paused = not paused
                elif event.key == K_UP:
                    time_scale = min(4.0, time_scale + 0.25)
                elif event.key == K_DOWN:
                    time_scale = max(0.1, time_scale - 0.25)

        # Deep Void Render Pass Setup
        glClearColor(0.01, 0.005, 0.015, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, (display[0] / display[1]), 1.0, 700.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Orbit Camera Trigonometry
        rad_yaw, rad_pitch = math.radians(cam_yaw), math.radians(cam_pitch)
        cx = cam_dist * math.sin(rad_yaw) * math.cos(rad_pitch)
        cy = cam_dist * math.sin(rad_pitch)
        cz = cam_dist * math.cos(rad_yaw) * math.cos(rad_pitch)
        gluLookAt(cx, cy, cz, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)

        # 1. Background Stars
        draw_starfield(stars)

        # 2. Relativistic Polar Jets
        draw_relativistic_jets(total_time)

        # 3. Accretion Infall Stream
        update_and_draw_infall_particles(particles, dt * time_scale, total_time)

        # 4. Main Accretion Disk (Keplerian Swirl + Doppler Beaming)
        draw_accretion_disk(total_time)

        # 5. Gravitational Lensing Bending Arcs (Over Top/Bottom of Horizon)
        draw_gravitational_lensing_arcs(total_time)

        # 6. Photon Sphere Glowing Shell
        draw_photon_sphere(quadric, radius=3.4, t=total_time)

        # 7. Central Event Horizon (Absolute Void Core)
        draw_event_horizon(quadric, radius=3.0)

        pygame.display.flip()

if __name__ == "__main__":
    main()