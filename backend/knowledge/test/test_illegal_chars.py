

import re
illegal_chars = r'[\\/:*?"<>|]'
content=re.sub(illegal_chars, '-', "开机之后无任何反应怎么办?")

print(content)



