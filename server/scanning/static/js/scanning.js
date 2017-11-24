var app = angular.module("scantool", []);
app.controller("boxCtrl", function ($scope, $http) {
	$scope.logUser;
	$scope.ipFiles = [];
	$scope.newTask_ipFiles_str = ""
	$scope.pluginFiles = []
	$scope.newTask_pluginFiles_str = "";
	$scope.newTask = {};//新任务信息
	$scope.activeNodes = [];
	$scope.activeNodesCheckedAll = false;
	$scope.participatingNodes = [];
	$scope.tasks = [];//所有任务

	//******************服务器通讯函数****get打头为从服务器获取数据，up打头为上传数据***********************


	$scope.getLogUser = function () {
		$http.get("/data/getLogUser").success(function (data) {
			$scope.logUser = data;
		});
	}


	//-------ip文件file相关---------------------------
	$scope.getIpFiles = function () {
		url = "/data/getIpFiles";

		$http.get(url).success(function (data) {
			for (var i = 0; i < data.length; i++) {

				var c = {};
				c.name = data[i];
				c.isChecked = false;//设定初始选中状态为false

				c.no = i;
				$scope.ipFiles.push(c);
			};


		});
	};
	$scope.upDeleteIpFile = function () {
		url = "/data/upDeleteIpFile?fileName=" + $scope.ipFileToDel_name;
		$http.get(url).success(function (data) {
			$scope.ipFiles = [];
			$scope.getIpFiles();
		});
		$scope.ipFileToDel_name = "";
	}


	//-------plugin文件file相关---------------------------
	$scope.upDeletePluginFile = function () {
		url = "/data/upDeletePluginFile?fileName=" + $scope.pluginFileToDel_name;
		$http.get(url).success(function (data) {
			$scope.pluginFiles = [];
			$scope.getPluginFiles();
		});
		$scope.pluginFileToDel = "";
	}

	$scope.getPluginFiles = function () {
		url = "/data/getPluginFiles";

		$http.get(url).success(function (data) {
			for (var i = 0; i < data.length; i++) {

				var c = {};
				c.name = data[i];
				c.isChecked = false;//设定初始选中状态为false

				c.no = i;
				$scope.pluginFiles.push(c);
			};


		});
	};



	//-------task相关---------------------------
	$scope.getTasks = function () {
		orderby = 'pubTime';
		url = "/data/getTasks?orderby=" + orderby;
		statusOptions = { "删除": -1, "未开始": 0, "执行": 1, "暂停": 2, "完成": 3 }
		$http.get(url).success(function (data) {
			$scope.tasks = data;
			console.log(data)
			for (var i = 0; i < $scope.tasks.length; i++) {
				$scope.tasks[i].description_lite = $scope.tasks[i].description.substr(0, 4) + "...";
				$scope.tasks[i].index = i;
				$scope.tasks[i].iconStartTask = true;
				if ($scope.tasks[i].ipTotal == null)
					$scope.tasks[i].progress = 0;
				else {
					finished = parseFloat($scope.tasks[i].ipFinished).toFixed(3)
					total = parseFloat($scope.tasks[i].ipTotal).toFixed(3)
					$scope.tasks[i].progress = finished / total * 100
				}

				switch ($scope.tasks[i].status) {
					case -1:
						$scope.tasks[i].status_string = "删除";
						break;
					case 0:
						$scope.tasks[i].status_string = "未开始";
						$scope.tasks[i].iconStartTask = true;
						break;
					case 1:
						$scope.tasks[i].status_string = "执行中";
						$scope.tasks[i].iconStartTask = false;
						break;
					case 2:
						$scope.tasks[i].status_string = "暂停";
						break;
					case 3:
						$scope.tasks[i].status_string = "完成";

						break;

				}
			}

		});
	}

	$scope.upNewTask = function () {

		$scope.newTask.user = $scope.logUser;
		if ($scope.newTask_ipFiles_str == "") {
			alert('请选择ip地址文件');
			return;
		}
		if ($scope.newTask_plugFiles_str == "") {
			alert('请选择插件！');
			return;
		}

		jsonstring = JSON.stringify($scope.newTask);
		url = "/data/upNewTask?newtask=" + jsonstring;
		$http.get(url).success(function (data) {
			$scope.newTask = null;
			var test = angular.element(document.getElementById('mb-confirm-newtask'));
			test.toggleClass("open");
			for (var i = 0; i < $scope.ipFiles.length; i++) {
				$scope.ipFiles[i].isChecked = false;
			}
			for (var i = 0; i < $scope.pluginFiles.length; i++) {
				$scope.pluginFiles[i].isChecked = false;
			}
		});


	};

	$scope.upDeleteTask = function (taskid) {
		url = "/data/upDeleteTask?taskid=" + taskid;
		$http.get(url).success(function (data) {
			$scope.getTasks();
		});

	}

	//-------nodes相关---------------------------
	$scope.getActiveNodes = function () {
		url = "/data/getActiveNodes";
		$http.get(url).success(function (data) {
			$scope.activeNodes = []
			for (var i = 0; i < data.length; i++) {
				console.log(data)
				var c = {};
				c.id = data[i].id;
				c.ipLeft = data[i].ipLeft;

				c.checked = false;//设定初始选中状态为false
				c.index = i
				console.log(c)

				$scope.activeNodes.push(c);

			};

		});
	};
	//*********************----------------------*******************

	//******************界面逻辑***************************

	$scope.chooseIpFile = function (no) {
		$scope.newTask_ipFiles_str = "";
		$scope.newTask.ipFiles = [];
		$scope.ipFiles[no].isChecked = !$scope.ipFiles[no].isChecked;
		for (var i = 0; i < $scope.ipFiles.length; i++) {
			if ($scope.ipFiles[i].isChecked) {
				$scope.newTask_ipFiles_str += $scope.ipFiles[i].name + "、";
				$scope.newTask.ipFiles.push($scope.ipFiles[i].name);
			}
		}
		$scope.newTask_ipFiles_str = $scope.newTask_ipFiles_str.substr(0, $scope.newTask_ipFiles_str.length - 1);

	}
	$scope.choosePluginFile = function (no) {
		$scope.newTask_pluginFiles_str = "";
		$scope.newTask.pluginFiles = [];
		$scope.pluginFiles[no].isChecked = !$scope.pluginFiles[no].isChecked;
		for (var i = 0; i < $scope.pluginFiles.length; i++) {
			if ($scope.pluginFiles[i].isChecked) {
				$scope.newTask_pluginFiles_str += $scope.pluginFiles[i].name + "、";
				$scope.newTask.pluginFiles.push($scope.pluginFiles[i].name);
			}
		}
		$scope.newTask_pluginFiles_str = $scope.newTask_pluginFiles_str.substr(0, $scope.newTask_pluginFiles_str.length - 1);
	}

	$scope.chooseActiveNode = function (no) {
		$scope.activeNodes[no].checked = !$scope.activeNodes[no].checked;
	}
	$scope.upStartTask = function () {
		//获取所有选中节点
		for (var i = 0; i < $scope.activeNodes.length; i++) {
			if ($scope.activeNodes[i].checked) {
				$scope.participatingNodes.push($scope.activeNodes[i].id)
			}
		}
		//获取选中任务
		id = $scope.chosedTaskId;
		index = $scope.choosedTaskIndex;

		// 提交服务器
		param = {}
		param['taskId'] = id;
		param['participatingNodes'] = ($scope.participatingNodes);
		jsonstring = JSON.stringify(param);
		url = "/data/upStartTask?param=" + jsonstring;
		$http.get(url).success(function (data) {
			console.log(data);
		});

		//更改页面
		$scope.tasks[index].status_string = '执行';
		$scope.tasks[index].iconStartTask = false;
		var test = angular.element(document.getElementById('mb-startTask'));
		test.modal('hide');

	}
	$scope.checkAllActiveNodes = function () {
		$scope.activeNodesCheckedAll = !$scope.activeNodesCheckedAll;
		if ($scope.activeNodesCheckedAll) {
			for (var i = 0; i < $scope.activeNodes.length; i++) {
				$scope.activeNodes[i].checked = true;
			};
		}
		else {
			for (var i = 0; i < $scope.activeNodes.length; i++) {
				$scope.activeNodes[i].checked = false;
			};
		}


	};



	$scope.openDelpluginFileConfirmMessageBox = function (name) {
		$scope.pluginFileToDel_name = name;
		var test = angular.element(document.getElementById('mb-confirm-delpluginfile'));
		test.toggleClass("open");
	}

	$scope.openDelIpFileConfirmMessageBox = function (name) {
		$scope.ipFileToDel_name = name;
		var test = angular.element(document.getElementById('mb-confirm-delipfile'));
		test.toggleClass("open");
	}
	$scope.startPauseTurn = function (id, index) {
		//获得选中任务
		$scope.choosedTaskIndex = index;
		$scope.chosedTaskId = id;
		//如果是play按钮，打开选择节点对话框
		if ($scope.tasks[index].iconStartTask) {
			if ($scope.tasks[index].status == 0) {
				$scope.getActiveNodes();
				var test = angular.element(document.getElementById('mb-startTask'));
				test.modal('show');
			}
			else if ($scope.tasks[index].status == 2) {
				$scope.tasks[index].iconStartTask = false
				$scope.tasks[index].status_string = '执行中';
			}
		}

		//如果是pause按钮，逻辑处理代码未写
		else {
			$scope.tasks[index].iconStartTask = true
			$scope.tasks[index].status == 2
			//todo:提交数据库
			$scope.tasks[index].status_string = '暂停';
		}
	}


	//*********************----------------------*******************

	//在加载页面时首先执行以下操作
	$scope.getLogUser();
	$scope.getTasks();
	$scope.getIpFiles();
	$scope.getPluginFiles();
	$scope.getActiveNodes();




});
