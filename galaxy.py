import sys
import math
import urllib.request
import io
import numpy as np
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image

# Vertex Shader: Transforms 3D geometry and passes view vectors
VS_CODE = """
#version 120
varying vec3 vNormal;
varying vec3 vViewDir;
varying vec2 vTexCoord;

void main() {
    vNormal = normalize(gl_NormalMatrix * gl_Normal);
    vec4 vertPos = gl_ModelViewMatrix * gl_Vertex;
    vViewDir = normalize(-vertPos.xyz);
    vTexCoord = gl_MultiTexCoord0.st;
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
}
"""

# Fragment Shader: Lommel-Seeliger Lunar Regolith Scattering Model
FS_CODE = """
#version 120
uniform sampler2D uTexture;
uniform vec3 uLightDirection;

varying vec3 vNormal;
varying vec3 vViewDir;
varying vec2 vTexCoord;

void main() {
    vec3 N = normalize(vNormal);
    vec3 L = normalize(uLightDirection);
    vec3 V = normalize(vViewDir);

    float NdotL = max(dot(N, L), 0.0);
    float NdotV = max(dot(N, V), 0.0);

    // Real Lunar Lommel-Seeliger scattering (prevents smooth glossy/Lambertian look)
    float lunarScattering = NdotL / (NdotL + NdotV + 0.05);
    
    // Smooth terminator shadow falloff
    float terminator = smoothstep(-0.02, 0.08, dot(N, L));

    vec4 texColor = texture2D(uTexture, vTexCoord);

    // Direct Sunlight illumination
    vec3 directSunlight = vec3(1.25, 1.22, 1.15) * lunarScattering * terminator;

    // Earthshine (faint blue-gray glow on the night side)
    vec3 earthshine = vec3(0.012, 0.016, 0.025) * (1.0 - terminator);

    vec3 finalColor = texColor.rgb * (directSunlight + earthshine);
    gl_FragColor = vec4(finalColor, 1.0);
}
"""

def generate_sphere_mesh(radius=1.8, stacks=120, slices=120):
    """Generates a high-resolution 3D sphere mesh."""
    vertices, normals, texcoords = [], [], []

    for i in range(stacks + 1):
        lat = math.pi * (-0.5 + float(i) / stacks)
        z0 = math.sin(lat)
        r0 = math.cos(lat)
        v = float(i) / stacks

        for j in range(slices + 1):
            lon = 2.0 * math.pi * float(j) / slices
            x0 = math.cos(lon) * r0
            y0 = math.sin(lon) * r0
            u = float(j) / slices

            vertices.extend([x0 * radius, y0 * radius, z0 * radius])
            normals.extend([x0, y0, z0])
            texcoords.extend([u, v])

    indices = []
    for i in range(stacks):
        for j in range(slices):
            first = i * (slices + 1) + j
            second = first + slices + 1
            indices.extend([first, second, first + 1])
            indices.extend([second, second + 1, first + 1])

    return (
        np.array(vertices, dtype=np.float32),
        np.array(normals, dtype=np.float32),
        np.array(texcoords, dtype=np.float32),
        np.array(indices, dtype=np.uint32)
    )

def generate_photorealistic_moon_map():
    """Generates a seamless 3D spherical noise map without polar distortion or circles."""
    width, height = 1024, 512
    u = np.linspace(0, 2 * np.pi, width, endpoint=False)
    v = np.linspace(-np.pi / 2, np.pi / 2, height)
    U, V = np.meshgrid(u, v)

    # Convert to 3D Cartesian coordinates to prevent UV polar distortion
    X = np.cos(V) * np.cos(U)
    Y = np.cos(V) * np.sin(U)
    Z = np.sin(V)

    # Multi-octave 3D spherical fractal noise
    noise = np.zeros((height, width), dtype=np.float32)
    octaves = [(1.8, 0.45), (3.5, 0.25), (7.0, 0.12), (14.0, 0.06), (28.0, 0.03)]

    for freq, amp in octaves:
        n = (np.sin(X * freq + 0.5) * np.cos(Y * freq + 0.2) +
             np.sin(Y * freq + 0.8) * np.cos(Z * freq + 0.4) +
             np.sin(Z * freq + 0.1) * np.cos(X * freq + 0.9))
        noise += n * amp

    # Scale Albedo: Dark Maria (volcanic plains) vs Light Lunar Highlands
    albedo = 0.42 + 0.32 * noise
    albedo = np.clip(albedo, 0.12, 0.85)

    gray = (albedo * 255).astype(np.uint8)
    return Image.fromarray(np.stack([gray, gray, gray], axis=-1))

def load_moon_texture():
    """Loads a NASA Clementine lunar map with procedural 3D noise fallback."""
    urls = [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/d/db/Moonmap_from_clementine_data.jpg/1024px-Moonmap_from_clementine_data.jpg",
        "https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720/lroc_color_poles_1k.jpg"
    ]
    
    img = None
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as resp:
                img = Image.open(io.BytesIO(resp.read())).convert("RGB")
                print("Successfully downloaded High-Res NASA Lunar Surface Map!")
                break
        except Exception:
            continue

    if img is None:
        print("Using spherical 3D procedural lunar surface texture...")
        img = generate_photorealistic_moon_map()

    img_data = img.tobytes("raw", "RGB", 0, -1)
    w, h = img.size

    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    
    try:
        gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGB, w, h, GL_RGB, GL_UNSIGNED_BYTE, img_data)
    except Exception:
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)
        glGenerateMipmap(GL_TEXTURE_2D)

    return tex_id

def create_shader_program():
    vs = glCreateShader(GL_VERTEX_SHADER)
    glShaderSource(vs, VS_CODE)
    glCompileShader(vs)

    fs = glCreateShader(GL_FRAGMENT_SHADER)
    glShaderSource(fs, FS_CODE)
    glCompileShader(fs)

    prog = glCreateProgram()
    glAttachShader(prog, vs)
    glAttachShader(prog, fs)
    glLinkProgram(prog)
    return prog

def generate_starfield(count=1600, dist=55.0):
    pts, colors = [], []
    for _ in range(count):
        theta = np.random.uniform(0, 2 * math.pi)
        phi = np.random.uniform(-0.5 * math.pi, 0.5 * math.pi)
        x = dist * math.cos(phi) * math.cos(theta)
        y = dist * math.sin(phi)
        z = dist * math.cos(phi) * math.sin(theta)
        b = np.random.uniform(0.2, 0.85)
        pts.extend([x, y, z])
        colors.extend([b, b, b])
    return np.array(pts, dtype=np.float32), np.array(colors, dtype=np.float32)

def calculate_lunar_phase(angle_deg):
    angle = angle_deg % 360.0
    illumination = (1.0 - math.cos(math.radians(angle))) / 2.0 * 100.0

    if angle < 22.5 or angle >= 337.5:
        phase = "New Moon"
    elif angle < 67.5:
        phase = "Waxing Crescent"
    elif angle < 112.5:
        phase = "First Quarter"
    elif angle < 157.5:
        phase = "Waxing Gibbous"
    elif angle < 202.5:
        phase = "Full Moon"
    elif angle < 247.5:
        phase = "Waning Gibbous"
    elif angle < 292.5:
        phase = "Third Quarter"
    else:
        phase = "Waning Crescent"

    return phase, illumination

def main():
    pygame.init()
    width, height = 1280, 720

    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)
    pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)

    pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("3D Realistic Lunar Phase Simulator")

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_TEXTURE_2D)
    glClearColor(0.001, 0.001, 0.003, 1.0)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45.0, (width / height), 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)

    tex_id = load_moon_texture()
    shader_prog = create_shader_program()
    vertices, normals, texcoords, indices = generate_sphere_mesh()
    star_pts, star_colors = generate_starfield()

    u_light_dir = glGetUniformLocation(shader_prog, "uLightDirection")
    u_texture = glGetUniformLocation(shader_prog, "uTexture")

    sun_angle = 0.0
    orbit_speed = 0.3
    paused = False

    cam_dist = 5.5
    cam_rot_x, cam_rot_y = 0.0, 0.0
    dragging = False
    last_mouse_pos = (0, 0)

    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_SPACE:
                    paused = not paused
                elif event.key == K_RIGHT:
                    orbit_speed += 0.15
                elif event.key == K_LEFT:
                    orbit_speed = max(0.05, orbit_speed - 0.15)
                elif event.key == K_r:
                    cam_rot_x, cam_rot_y, cam_dist = 0.0, 0.0, 5.5
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    dragging = True
                    last_mouse_pos = event.pos
                elif event.button == 4:
                    cam_dist = max(2.3, cam_dist - 0.3)
                elif event.button == 5:
                    cam_dist = min(12.0, cam_dist + 0.3)
            elif event.type == MOUSEBUTTONUP and event.button == 1:
                dragging = False
            elif event.type == MOUSEMOTION and dragging:
                dx = event.pos[0] - last_mouse_pos[0]
                dy = event.pos[1] - last_mouse_pos[1]
                cam_rot_y += dx * 0.4
                cam_rot_x += dy * 0.4
                cam_rot_x = max(-89.0, min(89.0, cam_rot_x))
                last_mouse_pos = event.pos

        if not paused:
            sun_angle = (sun_angle + orbit_speed) % 360.0

        phase_name, illumination = calculate_lunar_phase(sun_angle)
        pygame.display.set_caption(
            f"Phase: {phase_name} | Illumination: {illumination:.1f}% | Sun Angle: {sun_angle:.1f}°"
        )

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Camera Placement
        glTranslatef(0.0, 0.0, -cam_dist)
        glRotatef(cam_rot_x, 1.0, 0.0, 0.0)
        glRotatef(cam_rot_y, 0.0, 1.0, 0.0)

        # Background Starfield
        glUseProgram(0)
        glDisable(GL_TEXTURE_2D)
        glPointSize(1.2)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, star_pts)
        glColorPointer(3, GL_FLOAT, 0, star_colors)
        glDrawArrays(GL_POINTS, 0, len(star_pts) // 3)
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)

        # Render Moon
        glEnable(GL_TEXTURE_2D)
        glUseProgram(shader_prog)

        sun_rad = math.radians(sun_angle)
        lx, ly, lz = math.sin(sun_rad), 0.0, -math.cos(sun_rad)
        glUniform3f(u_light_dir, lx, ly, lz)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glUniform1i(u_texture, 0)

        glPushMatrix()
        glRotatef(6.68, 0.0, 0.0, 1.0)
        glRotatef(90, 0.0, 1.0, 0.0)

        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)

        glVertexPointer(3, GL_FLOAT, 0, vertices)
        glNormalPointer(GL_FLOAT, 0, normals)
        glTexCoordPointer(2, GL_FLOAT, 0, texcoords)

        glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, indices)

        glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)
        glPopMatrix()

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()