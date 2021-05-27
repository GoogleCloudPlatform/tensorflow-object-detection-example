'use strict';
        document.querySelector('.sub').addEventListener('click', function () {
            const guess = document.querySelector('.trsVal').value;

            console.log(guess, typeof guess);
        });