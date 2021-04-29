import os
if os.path.isdir("build"):
    from build.fixmorph.app import main
    if __name__ == "__main__":
        main.main()
else:
    from app import main
    if __name__ == "__main__":
        main.main()

