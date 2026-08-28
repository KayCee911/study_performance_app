let semestersList = [];
        let userEmail = '';
        
        // Initialize form
        async function initializeForm() {
            // Tokens removed â€” the add-course page is public. Identify user via form or default.
            
            await loadSemesters();
        }
        
        // Load user's semesters
        async function loadSemesters() {
            try {
                const response = await fetch('/api/semesters');
                
                if (!response.ok) {
                    console.log('Semesters endpoint not available, using manual entry');
                    return;
                }
                
                const data = await response.json();
                semestersList = data.semesters || [];
                
                // Populate semester dropdown
                const semesterSelect = document.getElementById('semester');
                semestersList.forEach(sem => {
                    const option = document.createElement('option');
                    option.value = sem.id;
                    option.textContent = sem.name;
                    semesterSelect.insertBefore(option, semesterSelect.querySelector('option[value="new"]'));
                });
            } catch (error) {
                console.log('Could not load semesters:', error);
            }
        }
        
        // Handle semester selection
        document.getElementById('semester').addEventListener('change', function(e) {
            const newSemesterGroup = document.getElementById('newSemesterGroup');
            const semesterNameInput = document.getElementById('semesterName');
            
            if (this.value === 'new') {
                newSemesterGroup.style.display = 'block';
                semesterNameInput.required = true;
            } else {
                newSemesterGroup.style.display = 'none';
                semesterNameInput.required = false;
                semesterNameInput.value = '';
            }
        });
        
        // Handle form submission
        async function handleSubmit(event) {
            event.preventDefault();
            
            const submitBtn = document.getElementById('submitBtn');
            const courseCode = document.getElementById('courseCode').value.trim();
            const courseName = document.getElementById('courseName').value.trim();
            const unit = document.getElementById('unit').value;
            const difficulty = document.getElementById('difficulty').value;
            const semester = document.getElementById('semester').value;
            const semesterName = document.getElementById('semesterName').value.trim();
            const studyHours = document.getElementById('studyHours').value.trim();
            const studyMethod = document.getElementById('studyMethod').value;
            
            // Validation
            if (!courseCode) {
                showAlert('Course code is required', 'error');
                return;
            }
            
            if (!unit || !difficulty) {
                showAlert('Please select units and difficulty level', 'error');
                return;
            }
            
            if (semester === 'new' && !semesterName) {
                showAlert('Semester name is required', 'error');
                return;
            }
            
            if (semester === '') {
                showAlert('Please select or create a semester', 'error');
                return;
            }
            
            // Show loading state
            submitBtn.classList.add('loading');
            submitBtn.disabled = true;
            
            try {
                const response = await fetch('/add-course', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        course_code: courseCode,
                        course_name: courseName,
                        unit: parseInt(unit),
                        difficulty: parseInt(difficulty),
                        semester_id: semester === 'new' ? null : parseInt(semester, 10),
                        semester_name: semester === 'new' ? semesterName : null,
                        study_hours: studyHours ? parseFloat(studyHours) : null,
                        study_method: studyMethod || 'Passive'
                    })
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    showAlert(data.error || 'Failed to add course', 'error');
                    submitBtn.classList.remove('loading');
                    submitBtn.disabled = false;
                    return;
                }
                
                // âœ… Display predictions
                displayPredictions(data);
                
            } catch (error) {
                showAlert('Error: ' + error.message, 'error');
                submitBtn.classList.remove('loading');
                submitBtn.disabled = false;
            }
        }
        
        // Display predictions and recommendations
        function displayPredictions(data) {
            const pred = data.prediction || {};
            
            // Update prediction values
            document.getElementById('currentGPA').textContent = (pred.current_gpa || 0).toFixed(2);
            document.getElementById('projectedGPA').textContent = (pred.projected_gpa || 2.5).toFixed(2);
            document.getElementById('recommendedHours').textContent = pred.recommended_study_hours || 3;
            document.getElementById('recommendedMethod').textContent = pred.recommended_method || 'Active';
            document.getElementById('suggestion').innerHTML = pred.suggestion || 'Study actively to improve your GPA';
            
            // Display explanations
            const explList = document.getElementById('explanationsList');
            explList.innerHTML = '';
            if (pred.explanations && Array.isArray(pred.explanations)) {
                pred.explanations.forEach(exp => {
                    const item = document.createElement('div');
                    item.className = 'explanation-item';
                    item.textContent = exp;
                    explList.appendChild(item);
                });
            } else {
                explList.innerHTML = '<div class="explanation-item">Continue with your current study approach</div>';
            }
            
            // Hide form, show results
            document.getElementById('courseForm').style.display = 'none';
            document.getElementById('predictionResult').classList.add('show');
            
            // Show success message
            showAlert(`âœ“ ${data.course.code} added! Predictions generated.`, 'success');
        }
        
        // Add another course
        function addAnother() {
            document.getElementById('courseForm').style.display = 'block';
            document.getElementById('predictionResult').classList.remove('show');
            document.getElementById('courseForm').reset();
            document.getElementById('newSemesterGroup').style.display = 'none';
            showAlert('Ready to add another course', 'success');
            window.scrollTo(0, 0);
        }
        
        // Show alert message
        function showAlert(message, type) {
            const alert = document.getElementById('alert');
            alert.className = `alert ${type} show`;
            alert.textContent = message;
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                alert.classList.remove('show');
            }, 5000);
        }
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', initializeForm);
