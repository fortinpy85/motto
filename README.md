# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/fortinpy85/motto/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                                  |    Stmts |     Miss |   Cover |   Missing |
|---------------------------------------------------------------------- | -------: | -------: | ------: | --------: |
| django/cache\_tiktoken.py                                             |        9 |        9 |      0% |      1-21 |
| django/chat/\_utils/estimate\_cost.py                                 |      133 |       22 |     83% |42, 52, 61-75, 79-81, 122, 135, 147, 169, 203-204, 216, 241 |
| django/chat/\_views/load\_test.py                                     |       77 |       49 |     36% |42, 60-108, 116-137, 158-198 |
| django/chat/\_views/pin\_chat.py                                      |       47 |       31 |     34% |18-36, 45-52, 57-66 |
| django/chat/forms.py                                                  |      239 |       49 |     79% |49, 56, 139-175, 180-181, 193-201, 240-246, 251, 263, 271-279, 566, 644-646, 666-690 |
| django/chat/llm.py                                                    |      208 |       58 |     72% |49, 53-63, 67-68, 88-90, 97, 123, 156-171, 174-176, 189-190, 194-199, 215-232, 318-321, 324-327, 385, 407, 421 |
| django/chat/llm\_models.py                                            |       74 |        6 |     92% |77, 83, 89, 170, 193, 207 |
| django/chat/models.py                                                 |      416 |       72 |     83% |182-191, 194-198, 311-314, 319-325, 333, 418, 487-491, 499-503, 509, 515, 521, 553, 580-581, 584, 591-595, 647, 651-653, 668, 679, 717, 721-740, 770-779, 783-784, 793-794, 804-805 |
| django/chat/prompts.py                                                |        5 |        0 |    100% |           |
| django/chat/responses.py                                              |      424 |      229 |     46% |67, 82, 92, 101, 180-185, 226-350, 368-406, 417, 426-427, 437, 513-515, 535-536, 541-602, 605-635, 691-694, 705-742, 745-748, 867-954, 971, 994-1062 |
| django/chat/tasks.py                                                  |       60 |        6 |     90% |    97-102 |
| django/chat/templatetags/chat\_extras.py                              |       20 |       13 |     35% |     18-33 |
| django/chat/utils.py                                                  |      498 |       93 |     81% |80, 107-109, 150, 162-163, 172-176, 188-194, 199-200, 210, 259, 283, 285-286, 297, 299-315, 320-332, 382-398, 448-450, 490, 513-514, 518-525, 533, 550-554, 590-600, 607, 902-903, 965, 967-972, 976, 1005-1007, 1014-1028 |
| django/chat/views.py                                                  |      626 |      184 |     71% |85-93, 106-108, 112-114, 120-136, 172, 185, 194, 211-213, 216-218, 248-279, 293-300, 306, 339-360, 457-461, 493-574, 600-601, 635, 639, 703, 723, 774-778, 823-825, 850-851, 932-933, 943, 985, 1076-1080, 1089, 1147-1184, 1194-1195, 1204-1209, 1253-1267, 1342-1406 |
| django/data\_fetcher/util.py                                          |        4 |        0 |    100% |           |
| django/import\_timer.py                                               |        6 |        6 |      0% |       1-8 |
| django/laws/forms.py                                                  |       77 |       17 |     78% |26-42, 54-70, 109 |
| django/laws/loading\_utils.py                                         |      290 |       83 |     71% |60-75, 131-135, 153, 186-189, 249, 267, 269, 271, 273, 291-292, 296-297, 299, 302, 304, 319-320, 322-323, 420-423, 433-451, 477-481, 493, 512, 564-565, 606-608, 702-820, 836, 843 |
| django/laws/loading\_views.py                                         |      106 |       17 |     84% |89-91, 170-173, 186, 250-260 |
| django/laws/management/commands/load\_laws\_xml.py                    |       97 |       55 |     43% |87-145, 157, 172, 174-175, 181-191 |
| django/laws/models.py                                                 |      232 |       36 |     84% |35, 78, 85-90, 112-116, 134-141, 149-154, 161, 188, 240-241, 318, 320, 333-341, 357, 436 |
| django/laws/prompts.py                                                |        4 |        0 |    100% |           |
| django/laws/tasks.py                                                  |      317 |      113 |     64% |48-51, 62, 128, 141, 143, 150, 166-169, 211-215, 224-225, 234-235, 287-301, 313-338, 351, 369-380, 400-406, 455-468, 508-509, 516-533, 546, 550-552, 555-557, 563-578 |
| django/laws/test\_retriever\_performance.py                           |       60 |       34 |     43% |58-59, 64-113, 117 |
| django/laws/translation.py                                            |        5 |        0 |    100% |           |
| django/laws/utils.py                                                  |       98 |       13 |     87% |24-26, 44, 90, 109-115, 132-136, 169 |
| django/laws/views.py                                                  |      304 |      146 |     52% |82, 86, 99, 109, 117-118, 124-215, 227, 243, 281, 283, 288-290, 297-323, 337, 373, 381, 389, 398, 442-443, 474-496, 548-561, 581-655 |
| django/librarian/forms.py                                             |      101 |        4 |     96% |125-126, 187, 205 |
| django/librarian/models.py                                            |      366 |       58 |     84% |53-55, 123, 125, 133, 135, 137, 147, 177-179, 201, 255, 317-318, 322-328, 334-337, 412, 429-438, 442, 460, 506-507, 529, 563-565, 580-588, 599-600, 610-611, 621-622, 634-635 |
| django/librarian/tasks.py                                             |      117 |       13 |     89% |70, 82, 143-144, 167-169, 180-183, 202-203 |
| django/librarian/translation.py                                       |        8 |        0 |    100% |           |
| django/librarian/utils/extract\_emails.py                             |      130 |       44 |     66% |68-82, 95-103, 107, 109, 117-127, 133-134, 138-141, 157, 160, 169-181, 191, 193 |
| django/librarian/utils/extract\_zip.py                                |       68 |       12 |     82% |37-39, 50-59, 92 |
| django/librarian/utils/markdown\_splitter.py                          |      185 |       10 |     95% |72, 75-77, 88, 126, 140, 263, 273, 280 |
| django/librarian/utils/process\_document.py                           |       21 |        1 |     95% |        35 |
| django/librarian/utils/process\_engine.py                             |      493 |       99 |     80% |57-64, 113, 187, 202-203, 207, 210, 213, 216, 223, 231, 239, 241, 243, 278, 293-294, 300, 302-304, 315, 317, 335-336, 352-363, 366-368, 385-411, 415-421, 431, 440-454, 499, 540-542, 588, 591-595, 601-605, 609, 650, 693, 760, 785, 796 |
| django/librarian/views.py                                             |      474 |      131 |     72% |37-41, 60-67, 126-147, 153, 169, 196-215, 230, 263, 325-326, 365, 371, 389, 404-408, 437-438, 444-445, 463, 474-475, 478, 491, 495-499, 529, 537-541, 544-546, 664, 669, 685-720, 757, 839-854, 858-903 |
| django/otto/celery.py                                                 |       16 |        1 |     94% |        94 |
| django/otto/context\_processors.py                                    |       18 |        4 |     78% |     10-13 |
| django/otto/forms.py                                                  |       76 |        4 |     95% |73, 75, 205-206 |
| django/otto/management/commands/delete\_empty\_chats.py               |       19 |        1 |     95% |        29 |
| django/otto/management/commands/delete\_old\_chats.py                 |       21 |        2 |     90% |    32, 36 |
| django/otto/management/commands/delete\_text\_extractor\_files.py     |       18 |        0 |    100% |           |
| django/otto/management/commands/delete\_unused\_libraries.py          |       21 |        2 |     90% |    32, 36 |
| django/otto/management/commands/reset\_app\_data.py                   |      126 |       22 |     83% |68-91, 104-109, 124, 141-146, 166-171, 185-186, 191-194, 209-214, 225 |
| django/otto/management/commands/test\_laws\_query.py                  |       52 |       38 |     27% |18-121, 128-135 |
| django/otto/management/commands/update\_exchange\_rate.py             |       19 |        0 |    100% |           |
| django/otto/management/commands/warn\_libraries\_pending\_deletion.py |       26 |        3 |     88% |     29-33 |
| django/otto/models.py                                                 |      296 |       27 |     91% |89-92, 167, 213, 216, 232, 253, 271, 378-381, 397, 400, 455, 462, 490, 494, 501, 507, 556-557, 571, 575, 579, 602 |
| django/otto/rules.py                                                  |      179 |        8 |     96% |46, 55, 121, 128, 156, 224-226 |
| django/otto/secure\_models.py                                         |      243 |       60 |     75% |61, 266-267, 339, 348, 367, 383, 388, 393, 399-406, 409, 414, 420-426, 429, 434, 439, 446-474, 477-478, 483-490, 493-494, 500-514, 528-529, 534-544, 549-550, 553-554 |
| django/otto/settings.py                                               |      148 |       27 |     82% |29-32, 39-44, 157-166, 243, 259, 318-325, 346, 439-440, 490 |
| django/otto/tasks.py                                                  |       54 |       13 |     76% |28, 48, 62, 67-70, 75-83 |
| django/otto/templatetags/filters.py                                   |       16 |        4 |     75% | 10, 23-25 |
| django/otto/templatetags/tags.py                                      |       10 |        1 |     90% |        18 |
| django/otto/translation.py                                            |       17 |        0 |    100% |           |
| django/otto/utils/common.py                                           |       72 |        4 |     94% |102, 132-134 |
| django/otto/utils/decorators.py                                       |       64 |        4 |     94% |26-27, 69, 92 |
| django/otto/utils/logging.py                                          |       15 |        0 |    100% |           |
| django/otto/utils/middleware.py                                       |       54 |        6 |     89% | 32, 93-97 |
| django/otto/utils/test\_auth\_middleware.py                           |       27 |        3 |     89% |     62-65 |
| django/otto/views.py                                                  |      638 |      187 |     71% |60, 65-66, 72-86, 122, 136, 147-157, 170, 306-307, 408, 425, 474-477, 493-494, 519, 529-537, 568-578, 590-595, 598, 607, 609-612, 614-615, 617-620, 643, 651, 660, 676-687, 793-794, 825, 827, 829, 843, 845, 852-853, 856-859, 869-875, 885, 887, 889, 894-914, 953, 962-971, 1050, 1058-1064, 1087-1088, 1096, 1102-1105, 1108, 1110, 1115-1125, 1129-1135, 1141-1219, 1239-1244, 1297-1299, 1319-1322 |
| django/postgres\_wrapper/base.py                                      |        6 |        0 |    100% |           |
| django/search\_history/models.py                                      |       21 |        3 |     86% |38, 43, 47 |
| django/search\_history/views.py                                       |       51 |       37 |     27% |15-37, 43-92, 99-104 |
| django/text\_extractor/models.py                                      |       18 |        1 |     94% |        29 |
| django/text\_extractor/tasks.py                                       |      104 |       61 |     41% |34-131, 163, 190, 198-214 |
| django/text\_extractor/utils.py                                       |      129 |       52 |     60% |53-76, 112-116, 155-199 |
| django/text\_extractor/views.py                                       |      163 |       45 |     72% |49, 67-75, 83-86, 109-131, 144-165, 180, 184, 192-213, 218, 223-228, 251, 257-258, 280-281, 304-306, 314 |
|                                                             **TOTAL** | **9136** | **2333** | **74%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/fortinpy85/motto/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/fortinpy85/motto/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/fortinpy85/motto/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/fortinpy85/motto/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Ffortinpy85%2Fmotto%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/fortinpy85/motto/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.