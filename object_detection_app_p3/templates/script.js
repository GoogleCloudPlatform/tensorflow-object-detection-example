document.querySelector('.submit').addEventListener('click', function () {
    const guess = Number(document.querySelector('.desicion').value);
    console.log(guess, typeof guess);
});