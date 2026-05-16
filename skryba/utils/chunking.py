from langchain_text_splitters import MarkdownHeaderTextSplitter


def readme_chunker(target: str) -> list[str]:
    """
    Readme chunker slice md files to smaller chunks.
    :param target: target md element in json to slice
    :return: list of chunks
    """
    headers_to_split_on = [("#", "Main header")]

    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on, strip_headers=False
    )

    md_header_splits = header_splitter.split_text(target)

    return [chunk.page_content for chunk in md_header_splits]
