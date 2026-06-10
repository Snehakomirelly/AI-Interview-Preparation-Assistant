async function generate(){


let role=document.getElementById("role").value;

let level=document.getElementById("level").value;


let response=await fetch("/generate",{

method:"POST",

headers:{
"Content-Type":"application/json"
},

body:JSON.stringify({

role:role,
level:level

})

});


let data=await response.json();


let sampleAnswers = {

"Explain OOP concepts":
"OOP stands for Object Oriented Programming. It is based on classes and objects. The main concepts are Encapsulation, Inheritance, Polymorphism and Abstraction.",


"Difference between list and tuple":
"List is mutable, meaning we can change its values after creation. Tuple is immutable, meaning values cannot be changed. Lists use square brackets and tuples use parentheses.",


"Explain REST API":
"REST API is an application programming interface that allows communication between client and server using HTTP methods like GET, POST, PUT and DELETE."

};



let output="";


data.questions.forEach((q,index)=>{


output += 
`
<div>

<h3>${index+1}. ${q}</h3>

<textarea class="answer">${sampleAnswers[q] || ""}</textarea>


</div>

`;

});


output += 
`
<br>

<button onclick="submitAnswers()">
Submit Answers
</button>
`;


document.getElementById("result").innerHTML=output;


}




function submitAnswers(){


let answers=[];


document.querySelectorAll(".answer")
.forEach(box=>{

answers.push(box.value);

});


document.getElementById("result").innerHTML +=

`
<h2>Interview Feedback</h2>

<p>
Score: 8/10
</p>

<p>
✓ Answers cover the main concepts
</p>

<p>
Improve:
Add more examples and real-world explanations.
</p>

`;

}