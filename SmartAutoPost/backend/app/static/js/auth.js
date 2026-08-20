/* =========================================================
   AUTH JS
   Login + Register + Social Login
   ========================================================= */


/* =========================================================
   LOGIN
   ========================================================= */


const loginForm =
document.getElementById("loginForm");


if(loginForm){


    loginForm.addEventListener(
        "submit",
        async function(e){


            e.preventDefault();



            const email =
            document.getElementById("email")
            .value
            .trim();



            const password =
            document.getElementById("password")
            .value;



            if(!email || !password){

                showToast(
                    "Email and password required",
                    true
                );

                return;
            }



            try{


                const data =
                await api(
                    "/auth/login",
                    {

                        method:"POST",

                        body:JSON.stringify({

                            email:email,

                            password:password

                        })

                    }
                );



                localStorage.setItem(
                    "access_token",
                    data.access_token
                );



                if(data.refresh_token){

                    localStorage.setItem(
                        "refresh_token",
                        data.refresh_token
                    );

                }



                if(data.user){

                    localStorage.setItem(
                        "user",
                        JSON.stringify(data.user)
                    );

                }



                showToast(
                    "Login successful"
                );



                setTimeout(()=>{

                    window.location.href="/dashboard";

                },1000);



            }
            catch(error){


                showToast(
                    error.message,
                    true
                );


            }



        }
    );

}




/* =========================================================
   REGISTER
   ========================================================= */



const registerForm =
document.getElementById(
    "registerForm"
);



if(registerForm){


    registerForm.addEventListener(
        "submit",
        async function(e){


            e.preventDefault();



            const name =
            document.getElementById(
                "name"
            )
            .value
            .trim();



            const email =
            document.getElementById(
                "email"
            )
            .value
            .trim();



            const password =
            document.getElementById(
                "password"
            )
            .value;




            if(
                !name ||
                !email ||
                !password
            ){


                showToast(
                    "All fields are required",
                    true
                );


                return;

            }





            try{


                console.log(
                    "Register API calling..."
                );



                const data =
                await api(
                    "/auth/register",
                    {


                        method:"POST",


                        body:JSON.stringify({

                            name:name,

                            email:email,

                            password:password

                        })


                    }
                );




                console.log(
                    "Register response",
                    data
                );




                showToast(
                    "Registration successful"
                );




                setTimeout(()=>{


                    window.location.href =
                    "/login";


                },1500);



            }
            catch(error){


                console.log(
                    error
                );


                showToast(
                    error.message,
                    true
                );


            }




        }
    );


}




/* =========================================================
   SOCIAL LOGIN
   ========================================================= */


function socialLogin(provider){


    window.location.href =
    `/api/v1/auth/${provider}/login`;


}