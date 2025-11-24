// frontend/flask_app/static/js/app.js
document.addEventListener('DOMContentLoaded', function(){
  // smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(a=>{
    a.addEventListener('click', function(e){
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if(target) target.scrollIntoView({behavior:'smooth', block:'start'});
    });
  });

  // jump from "Try Demo" to verify
  const jump = document.getElementById('jump-verify');
  if(jump) jump.addEventListener('click', e=>{
    // default anchor behavior will do
  });
});
