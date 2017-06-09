import curses
import hexes
import util

def render_list(win, lst, sel, listStart, listHeight, width, render_entry):
    
    util.log('render_list', lst)

    # selected index
    curIndex = 0 if sel == None else lst.index(sel)

    # scroll
    offset = curIndex - int(listHeight / 2)
    if offset < 0: offset = 0
    if offset > len(lst) - listHeight: offset = len(lst) - listHeight

    # render in box    
    for i in range(0, listHeight):
        
        io = offset + i
        if io < 0 or io >= len(lst):
            continue
    
        render_entry(i + listStart, lst[io], lst[io] == sel)

    # cursor indicator    
    if sel != None:
        cursorText = '#' + str(curIndex) + '/' + str(len(lst))
        win.addnstr(listStart, width-len(cursorText), cursorText, len(cursorText), curses.A_REVERSE)
    