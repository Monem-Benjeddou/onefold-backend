def guess_file_type_by_extension(file_name: str) -> str:
    """
    Guess the file type by the extension of the file name.
    :param file_name: str
    :return: str
    """
    file_extension = file_name.split(".")[-1].lower()
    if file_extension in ["pdf"]:
        return "application/pdf"
    if file_extension in ["doc", "docx"]:
        return "application/msword"
    if file_extension in ["xls", "xlsx"]:
        return "application/vnd.ms-excel"
    if file_extension in ["ppt", "pptx"]:
        return "application/vnd.ms-powerpoint"
    if file_extension in ["jpg", "jpeg", "png", "gif"]:
        return "image"
    if file_extension in ["mp4", "avi", "mkv", "webm"]:
        return "video"
    if file_extension in ["mp3", "wav", "flac", "ogg"]:
        return "audio"
    return "text"
