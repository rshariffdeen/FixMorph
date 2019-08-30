def verification():
    if Common.crash_script != None:
        try:
            Pc.make(bear=False)
        except Exception as e:
            Print.warning("Make failed.")
            Print.warning(e)
            restore_files()
            err_exit("Crochet failed at patching. Project did not compile" + \
                     "after changes. Exiting.")
        try:
            c = "sh " + Common.crash_script
            exec_com(c)
        except Exception as e:
            Print.warning("Crash gave an error.")
            Print.warning(e)
            restore_files()
            err_exit("Crochet failed at patching. Project still Common.crash_scripted" + \
                     "after changes. Exiting.")
    # TODO: Remove this part when we don't care anymore

    restore_files()


def safe_exec(function_def, title, *args):
    start_time = time.time()
    Print.title("Starting " + title + "...")
    description = title[0].lower() + title[1:]
    try:
        if not args:
            result = function_def()
        else:
            result = function_def(*args)
        duration = str(time.time() - start_time)
        Print.success("Successful " + description + ", after " + duration + " seconds.")
    except Exception as exception:
        duration = str(time.time() - start_time)
        Print.error("Crash during " + description + ", after " + duration + " seconds.")
        err_exit(exception, "Unexpected error during " + description + ".")
    return result

