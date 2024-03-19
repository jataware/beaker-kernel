
export function focusSelectedCell(ref) {
    let parent = document;
    if (ref && ref.value){
      parent = ref.value;
    }
    const elem: HTMLElement = parent.querySelector('.beaker-cell.selected');
    if (elem) {
        elem.focus();
    }
}
