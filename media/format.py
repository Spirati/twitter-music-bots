from os import listdir,mkdir
from shutil import rmtree
import subprocess

generate_ffmpeg_string = lambda filename,cover,album: f'ffmpeg -nostdin -y -loglevel error -loop 1 -i "input/{cover}" -i "input/{filename}" -filter:v "fps=30,scale=w=480:h=480" -tune stillimage -c:a aac -c:v libx264 -b:a 192k -pix_fmt yuv420p -t 140 -shortest "out/{album} - {filename}-process.mp4"'

def chunk(l, size):
    return [l[size*i:size*(i+1)] for i in range(len(l)//size+1)]

def process_files():
    album = input("Please provide an album label to be added to every song in the input (e.g. Octopath Traveler): ")

    files = listdir("./input")
    cover = None
    songs = []
    if "cover" not in [name.lower().split(".")[0] for name in files if any(x in name for x in ["jpg", "png"])]:
        print("Missing a cover file")
    else:
        cover = files[[i for i,n in enumerate(files) if "cover" in n.lower() and any(x in n for x in ["jpg", "png"])][0]]
        songs = [song for song in files if song != cover]
    try:
        mkdir("out")
    except:
        rmtree("out")
        mkdir("out")
        print("Removed previous files")
    
    print("Processing all songs. THIS WILL TAKE SOME TIME.")
    for batch in chunk(songs, 4):
        procs = [(song,subprocess.Popen(generate_ffmpeg_string(song, cover,album), shell=True)) for song in batch]
        for s,p in procs:
            p.wait()
            print(s)
    print("Done processing. Starting helper server.")